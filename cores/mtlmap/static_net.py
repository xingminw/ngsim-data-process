"""
This file contains the classes and load/save of the OSM (XML) data
    see more information for the OSM (XML) data: https://wiki.openstreetmap.org/wiki/OSM_XML
    highly recommended map edit software: JSOM | https://josm.openstreetmap.de/

"""
import numpy as np
import networkx as nx
import pandas as pd

from .map_modes import GraphMode
from .nodes_classes import NodeCategory
from ..utils.geometry import BoundingBox


class Network(object):
    """
    Class for the general network

    **Main Attributes**
        Classes for the roads
            - ``.ways``: a dictionary contains all the OpenStreetMap ways (:class:`mtldp.mtlmap.OsmWay`) in the network.
            - ``.links`` a dictionary contains all the links (:class:`mtldp.mtlmap.Link`) in the network.
            - ``.segments`` a dictionary contains all the segments (:class:`mtldp.mtlmap.Segment`) in the network.
            - ``.lanesets`` a dictionary contains all the lanesets (:class:`mtldp.mtlmap.LaneSet`) in the network.
        Classes for the nodes
            - ``.nodes`` a dictionary contains all the nodes (:py:class:`mtldp.mtlmap.Node`) in the network
        Others
            - ``.bounds`` the bounding box of the network, `mtldp.utils.BoundingBox`
            - ``.networkx_graph`` networkx graph
    """

    def __init__(self, region_name, city_id=''):

        self.region_name = region_name
        self.city_id = city_id
        # basic members
        self.segments = {}
        self.ways = {}
        self.nodes = {}
        self.links = {}
        self.movements = {}
        self.arterials = {}
        self.lanes = {}

        # the following content is for network modeling
        self.lanesets = {}
        self.connectors = {}
        self.conflict_points = {}
        self.lane_connectors = {}

        self.signalized_node_list = []
        self.unsignalized_node_list = []
        self.end_node_list = []

        self.networkx_mode = GraphMode.SEGMENT
        self.networkx_graph = None
        self.bounds = None

    def shortest_path_between_nodes(self, source_node: str, end_node: str,
                                    weight_attrib: str = "length"):
        """
        Calculate the shortest path between **unordinary nodes** (the source node and end node
        should not be an ordinary node). This implementation is based on NetworkX.

        .. attention::
            Please pay attention to the NetworkX graph mode, there are different modes for building the networkX graph
            and the shortest path function also differs under different mode. See :class:`mtldp.mtlmap.GraphMode` for
            more information.

        :param source_node: source node id
        :param end_node: end node id
        :param weight_attrib: the chosen weight to calculate the shortest path
        :return: ``{"nodes": [str], "weight": float, "edges": [str]}``, ``"weight"`` is ``None`` if no connected path.
        """
        if self.networkx_graph is None:
            self.build_networkx_graph()

        graph = self.networkx_graph

        # dump the weight to the directed graph
        for edge, edge_attribs in graph.edges.items():
            road_segment = edge_attribs["obj"]
            if not (weight_attrib in road_segment.__dict__.keys()):
                raise ValueError(weight_attrib + " not exist")
            graph.edges[edge]["weight"] = getattr(road_segment, weight_attrib)

        if self.networkx_mode == GraphMode.SEGMENT or self.networkx_mode == GraphMode.LINK:
            node_list = nx.shortest_path(graph, source_node, end_node, "weight")
            total_weight = 0
            edge_list = []
            for idx in range(len(node_list) - 1):
                source_n = node_list[idx]
                end_n = node_list[idx + 1]
                total_weight += graph.edges[source_n, end_n, 0]["weight"]
                if self.networkx_mode == GraphMode.SEGMENT:
                    edge_list.append(graph.edges[source_n, end_n, 0]["obj"].segment_id)
                else:
                    edge_list.append(graph.edges[source_n, end_n, 0]["obj"].link_id)
            output_dict = {"weight": total_weight, "nodes": node_list, "edges": edge_list}
            return output_dict
        else:
            node = self.nodes[source_node]
            source_lanesets = node.downstream_lanesets
            node = self.nodes[end_node]
            end_lanesets = node.upstream_lanesets
            total_weight_list = []
            output_dict_list = []
            for source_laneset in source_lanesets:
                for end_laneset in end_lanesets:
                    try:
                        laneset_list = nx.shortest_path(graph, source_laneset, end_laneset, "weight")
                        total_weight = 0
                        node_list = []
                        for idx, laneset_id in enumerate(laneset_list):
                            laneset = self.lanesets[laneset_id]
                            total_weight += getattr(laneset, weight_attrib)
                            node_list.append(self.lanesets[laneset_id].downstream_node)
                        output_dict = {"weight": total_weight, "nodes": node_list, "edges": laneset_list}
                        total_weight_list.append(total_weight)
                        output_dict_list.append(output_dict)
                    except nx.exception.NetworkXNoPath:
                        # could not find shortest path by networkx
                        total_weight = 1e8
                        output_dict = {"weight": total_weight, "nodes": [], "edges": []}
                        total_weight_list.append(total_weight)
                        output_dict_list.append(output_dict)

            chosen_index = int(np.argmin(total_weight_list))
            weight_ans = total_weight_list[chosen_index]
            if weight_ans >= 1e8 - 2:
                return {"weight": None, "nodes": [], "edges": []}
            else:
                return output_dict_list[chosen_index]

    def build_networkx_graph(self, graph_mode: "mtldp.mtlmap.GraphMode" = GraphMode.SEGMENT,
                             networkx_type: int = 0):
        """
        Build the self to a NetworkX graph object

        See reference for networkx: https://networkx.org/, this package will allow you
        to apply different types of algorithms based on network including shortest path, etc.

        :param networkx_type: graph type, 0: MultiDiGraph, 1: DiGraph
        :param graph_mode: the chosen graph mode, see :class:`mtldp.mtlmap.GraphMode`
        """
        if networkx_type == 0:
            graph = nx.MultiDiGraph()
        else:
            graph = nx.DiGraph()

        if graph_mode == GraphMode.SEGMENT:
            self.networkx_mode = GraphMode.SEGMENT
            # segment level graph, the ordinary nodes will be ignored
            for node_id, node in self.nodes.items():
                if node.is_ordinary_node():
                    continue
                graph.add_node(node_id, pos=(node.longitude, node.latitude))
            for segment_id, segment in self.segments.items():
                graph.add_edge(segment.upstream_node.node_id, segment.downstream_node.node_id, obj=segment)
        elif graph_mode == GraphMode.LINK:
            # print("This is not recommended unless you have special need to generate"
            #       " the networkX object based on link level segmentation")
            self.networkx_mode = GraphMode.LINK
            # link level graph, only the intersection node will be considered
            for node_id, node in self.nodes.items():
                if node.is_intersection() or node.type == NodeCategory.END:
                    graph.add_node(node_id, pos=(node.longitude, node.latitude))
            for link_id, link in self.links.items():
                graph.add_edge(link.upstream_node.node_id, link.downstream_node.node_id, obj=link)
        elif graph_mode == GraphMode.LANESET:
            raise NotImplementedError('LaneSet level shortest path not implemented yet')
        else:
            raise ValueError("Input mode not correct for building networkx graph.")

        self.networkx_graph = graph

    def reset_bound(self):
        """
        Reset the boundary to be the min and max of the longitudes and latitudes

        :return: None
        """
        lat_list = []
        lon_list = []
        for node_id, node in self.nodes.items():
            lat_list.append(node.latitude)
            lon_list.append(node.longitude)

        self.bounds = BoundingBox(np.round(np.min(lon_list), 5), np.round(np.min(lat_list), 5),
                                  np.round(np.max(lon_list), 5), np.round(np.max(lat_list), 5))

    def load_spat(self, spat_collection):
        """
        Load SPaT data into the network

        :param spat_collection: `mtldp.mtlmap.SPaTCollection`
        :return: None
        """
        for movement_id, movement in self.movements.items():
            node_id = movement.node.node_id
            if not (node_id in spat_collection.node_spats.keys()):
                movement.spat = None
                continue
            print(f"Node {node_id}, movement {movement_id} is matched.")
            movement_spat = spat_collection.node_spats[node_id].get_movement_spat(movement_id)
            movement.spat = movement_spat

    def get_movement_df(self, attributes, attr2str=False):
        """
        Save the given attributes of movements in the network to df

        :param attributes: the attributes to be saved in df
        :param attr2str: True if the users wants to save hte attributes as str
        :return: `pandas.DataFrame`
        """
        df = pd.DataFrame(columns=["movement_id"] + attributes)
        for movement_id, movement in self.movements.items():
            movement_info_dict = {"movement_id": movement_id}
            for attr in attributes:
                if attr in movement.__dict__.keys():
                    if not attr2str:
                        movement_info_dict[attr] = getattr(movement, attr)
                    else:
                        movement_info_dict[attr] = str(getattr(movement, attr))
            df = df.append(movement_info_dict, ignore_index=True)
        return df

    def overload_movement_df(self, df, attributes=None):
        """
        Change the given attribute of movements in network to be the attributes in df

        :param df: `pandas.DataFrame`
        :param attributes: list of attributes name
        :return: None
        """
        if attributes is None:
            attributes = df.columns

        row_dict_list = df.to_dict(orient="records")
        for row_dict in row_dict_list:
            movement_id = row_dict["movement_id"]
            for k, v in row_dict.items():
                if k == "movement_id":
                    continue

                if not (k in attributes):
                    continue

                if movement_id in self.movements.keys():
                    setattr(self.movements[movement_id], k, v)

    @staticmethod
    def add_segment_connection(upstream_segment, downstream_segment):
        """
        Add a connection to the given two segments

        :param upstream_segment: :class:`mtldp.mtlmap.Segment`
        :param downstream_segment: :class:`mtldp.mtlmap.Segment`
        :return: None
        """
        # segment = self.segments[upstream_segment_id]
        upstream_segment.add_downstream_segment(downstream_segment)
        # segment = self.segments[downstream_segment_id]
        downstream_segment.add_upstream_segment(upstream_segment)

    def add_laneset(self, laneset):
        self.lanesets[laneset.laneset_id] = laneset

    def add_way(self, osm_way):
        self.ways[osm_way.way_id] = osm_way

    def add_connector(self, connector):
        self.connectors[connector.connector_id] = connector

    def add_lane_connector(self, lane_connector):
        self.lane_connectors[lane_connector.connector_id] = lane_connector

    def add_node(self, node):
        self.nodes[node.node_id] = node

    def add_lane(self, lane):
        self.lanes[lane.lane_id] = lane

    def add_segment(self, segment):
        self.segments[segment.segment_id] = segment

    def add_link(self, link, repeat_add_name=None):
        """

        :param link:
        :param repeat_add_name: string, for repeat cycle name, add additional part to it
        :return:
        """
        if repeat_add_name is None:
            self.links[link.link_id] = link
        else:
            if link.link_id in self.links.keys():
                link.link_id += repeat_add_name
                self.links[link.link_id] = link
            else:
                self.links[link.link_id] = link

    def add_movement(self, movement):
        self.movements[movement.movement_id] = movement

    def add_arterial(self, arterial):
        self.arterials[arterial.arterial_id] = arterial

    def add_conflict_point(self, conflict_point):
        self.conflict_points[conflict_point.conflict_id] = conflict_point

    def get_link_id(self):
        return list(self.links.keys())

    def get_node_type(self, node_id: str) -> str:
        """
        Get the node type

        :param node_id: node id
        :return: str, the type of the node
        """
        return self.nodes[node_id].type
