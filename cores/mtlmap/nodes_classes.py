"""

"""
from enum import Enum


class NodeCategory(Enum):
    ORDINARY = 0
    CONNECTOR = 1
    SIGNALIZED = 2
    UNSIGNALIZED = 3
    END = 4


class Node(object):
    def __init__(self, node_id=None, osm_attrib=None, osm_tags=None):
        # original osm data (essential components)
        self.node_id = node_id
        self.osm_attrib = osm_attrib
        self.osm_tags = osm_tags
        self.type = NodeCategory.ORDINARY
        self.latitude = None
        self.longitude = None
        self.name = None

        self.connector_list = []

        # upstream and downstream segments
        self.upstream_segments = []
        self.downstream_segments = []

        # upstream and downstream links
        self.upstream_links = []
        self.downstream_links = []

        # upstream and downstream lanesets
        self.upstream_lanesets = []
        self.downstream_lanesets = []

        self.upstream_lanes = []
        self.downstream_lanes = []
        self.movement_list = []
        self.belonged_sup_arterial = []

        # osm way id that starts/ends at this node
        self.od_ways = []
        # in original osm data, some segments might directly traverse the node, this is
        # invalid, we need to filter this condition out by splitting the traversing segments
        self.traverse_ways = []

        if self.node_id is not None and self.osm_attrib is not None \
                and self.osm_tags is not None:
            self.generate_basic_info()

    def is_intersection(self) -> bool:
        """
        Check if a node is an intersection

        :return: True if this node is an intersection
        """
        intersection_flag = (self.type == NodeCategory.SIGNALIZED) or (self.type == NodeCategory.UNSIGNALIZED)
        return intersection_flag

    def is_ordinary_node(self) -> bool:
        """
        Check if a node is an ordinary node

        :return: True if this node is an ordinary node
        """
        return self.type == NodeCategory.ORDINARY

    def generate_basic_info(self):
        """
        Add latitude and longitude attributes

        :return: None
        """
        self.latitude = float(self.osm_attrib["lat"])
        self.longitude = float(self.osm_attrib["lon"])

    def add_connector(self, connector):
        """
        Add connector to the node

        :param connector: `mtldp.mtlmap.Connector`
        :return: None
        """
        exist_connector_id_list = [con.connector_id for con in self.connector_list]
        if not (connector.connector_id in exist_connector_id_list):
            self.connector_list.append(connector)

    def add_movement(self, movement):
        """
        Add a movement to the node

        :param movement: `mtldp.mtlmap.Movement`
        :return:
        """
        movement_id_list = [mov.movement_id for mov in self.movement_list]
        if movement.movement_id not in movement_id_list:
            self.movement_list.append(movement)

    def del_upstream_segment(self, segment_id):
        """
        delete the upstream segment id

        :param segment_id:
        :return:
        """
        del_idx = None
        count = 0
        for segment in self.upstream_segments:
            if str(segment) == segment_id:
                del_idx = count
            count += 1
        if del_idx is not None:
            del self.upstream_segments[del_idx]

    def __str__(self):
        return self.node_id


def update_node_index(network):
    """
    Update the index of nodes in a network
    fixme: this function is deprecated! We might no longer need to reset the node index

    :param network: `mtldp.mtlmap.Network`
    :return: `mtldp.mtlmap.Network`
    """
    for way_id, way in network.ways.items():
        new_node_list = []
        for node in way.node_list:
            new_node_list.append(network.nodes[node.node_id])
        way.upstream_node = new_node_list[0]
        way.downstream_node = new_node_list[-1]
        way.node_list = new_node_list

    for segment_id, segment in network.segments.items():
        new_node_list = []
        for node in segment.node_list:
            new_node_list.append(network.nodes[node.node_id])
        segment.node_list = new_node_list
        segment.upstream_node = new_node_list[0]
        segment.downstream_node = new_node_list[-1]
        # print([node.type for node in new_node_list])
    return network


def node_differentiation(network):
    """
    differentiate the node into:
        ordinary node, signalized intersection and unsignalized intersection

    :param network: `mtldp.mtlmap.Network`
    :return: `mtldp.mtlmap.Network`
    """
    signalized_nodes = []
    end_nodes = []
    unsignalized_nodes = []

    for node_id, node in network.nodes.items():
        undirected_degree = 2 * len(node.traverse_ways) + len(node.od_ways)
        if undirected_degree == 1:
            end_nodes.append(node)
            node.type = NodeCategory.END
        elif undirected_degree == 2:
            pass
        else:
            node_tags = node.osm_tags
            signalized_flag = False
            if "highway" in node_tags.keys():
                if node_tags["highway"] == "traffic_signals":
                    signalized_flag = True
            if signalized_flag:
                signalized_nodes.append(node)
                node.type = NodeCategory.SIGNALIZED
            else:
                unsignalized_nodes.append(node)
                node.type = NodeCategory.UNSIGNALIZED

    # save node list to network
    network.unsignalized_node_list = unsignalized_nodes
    network.end_node_list = end_nodes
    network.signalized_node_list = signalized_nodes
    return network

def infer_node_name(network):
    """
    Infer name of the nodes in a network

    :param network: `mtldp.mtlmap.Network`
    :return: `mtldp.mtlmap.Network`
    """
    for node_id, node in network.nodes.items():
        if not node.is_intersection():
            continue

        if node.name is not None:
            continue
        movement_list = node.movement_list
        vertical_name = None
        horizontal_name = None
        for movement in movement_list:
            upstream_link = movement.upstream_link
            segment = upstream_link.segment_list[-1]
            osm_tags = segment.osm_tags
            if "name" in osm_tags.keys():
                road_name = osm_tags["name"]
            else:
                road_name = None

            if movement.index in [1, 2, 5, 6]:
                if vertical_name is None:
                    if road_name is not None:
                        vertical_name = road_name
            elif movement.index in [3, 4, 7, 8]:
                if horizontal_name is None:
                    if road_name is not None:
                        horizontal_name = road_name
        node.name = f"{vertical_name}/{horizontal_name}"
    return network


def _set_attributes_from_dict(node, input_dict, network_component_dict, key_name):
    node_dict = node.__dict__
    if input_dict.get(key_name) is not None and len(input_dict.get(key_name)) != 0:
        target_list = input_dict[key_name].split(";")
        for value_id in target_list:
            value_obj = network_component_dict[value_id]
            node_dict[key_name].append(value_obj)


def generate_node_connections(network):
    for segment_id, segment in network.segments.items():
        downstream_node = segment.downstream_node
        upstream_node = segment.upstream_node
        print(downstream_node)
        network.nodes[downstream_node].upstream_segments.append(segment)
        network.nodes[upstream_node].downstream_segments.append(segment)

    return network