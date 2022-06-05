import json

from copy import deepcopy
from .laneset import LaneSet
from .nodes_classes import NodeCategory

from ..utils import logger
from ..utils import constants as mapping
from ..utils.gps_utils import shift_geometry
from ..utils.geometry import Geometry


class Segment(object):
    """
    A segment is a proportion of a link that share share the same number of lanes.

    **Main attributes**
        - ``.segment_id`` a integer for segment ID. 0 or 1 (denotes the direction ) is added at the end of the
          ``.osm_way`` as the ``.segment_id``
        - ``.osm_way`` a integer for the original OSM way ID
        - ``.osm_tags`` a dictionary contains all the tags in the original osm data.
        - ``.osm_attrib`` a dictionary contains all the attributes in the original osm data.
        - ``.belonged_link`` the link ID that the segment belongs to
        - ``.laneset_list`` the list of lane sets that belong to the segment
        - ``.laneset_num`` the number of lane sets that belong to the segment
        - ``.speed_limit`` speed limit of the segment in m/s
        - ``.length`` length of the segment in meters
        - ``.geometry`` the GPS coordinates along the segment
        - ``.lane_number`` number of lanes of the segment
        - ``.lane_assignment`` the assignment of the lanes of the segment. For example, "all_through" means all lanes on
          the segment are through movements. "left|through;right" means the segments include both left turn movement
          through (right turn) movement. If unavailable, this value is null.
        - ``.heading`` the heading angle of the segment (range: (-180,180]))
        - ``.from_direction`` the direction from which the segment originates. For example, if the segment originates
          from south, this value is "S".
        - ``.node_list`` a list of nodes on the segment
        - ``.upstream_node`` the upstream node of the segment
        - ``.downstream_node`` the downstream node of the segment
        - ``.upstream_segment`` a list of the upstream segment ID of this segment
        - ``.downstream_segment`` a list of the downstream segment ID of this segment
        - ``.downstream_direction_info`` a dictionary that represents the direction of the downstream segments.
          For example, ``{'l': '4116329441', 'r': '4126838890', 's': '87279680'}`` means left turn downstream segment is
          ``4116329441``. Through movement downstream segment is ``87279680``, and right turn downstream segment is
          ``4126838890``

    """

    def __init__(self):
        self.segment_id = None
        self.osm_way = None

        self.osm_tags = None
        self.osm_attrib = None

        self.belonged_link = None

        self.laneset_list = []
        self.lane_list = []
        self.laneset_num = None

        self.osm_direction_flag = None  # "backward" or "forward"
        self.speed_limit = None
        self.length = None  # unit: meters
        self.geometry = None  # `mtldp.utils.Geometry`
        self.lane_number = None
        self.lane_assignment = None

        self.heading = None
        # self.weighted_heading = None
        self.from_direction = None
        self.node_list = None

        # network topology
        self.upstream_node = None
        self.downstream_node = None

        self.downstream_connectors = []
        self.upstream_connectors = []

        self.upstream_segments = []
        self.downstream_segments = []
        self.downstream_directions_info = {}

    @classmethod
    def init_from_way(cls, osmway, direction):
        """
        Initiate a segment using the osm way

        Important attributes include:
        1) oneway = yes or no
        2) # of lanes
        3) turn direction of the lanes

        :param osmway: :class:`mtldp.mtlmap.Osmway`
        :param direction: "backward" or "forward"
        :return: `None`
        """
        segment = cls()
        if direction == "forward":
            segment.segment_id = osmway.way_id + "0"
        else:
            segment.segment_id = osmway.way_id + "1"

        segment.osm_direction_flag = direction
        segment.osm_way = osmway
        segment.length = osmway.length
        segment.speed_limit = osmway.speed_limit

        # get the osm tag and attributes
        segment.osm_tags = deepcopy(osmway.osm_tags)
        segment.osm_attrib = deepcopy(osmway.osm_attrib)

        # change the osm tags and attributes
        segment.osm_tags["oneway"] = "yes"
        if "action" in osmway.osm_attrib:
            segment.osm_attrib["action"] += "-directed"
        segment.osm_attrib["id"] = segment.segment_id

        # todo: reverse the direction, I am not sure whether it will be used but
        way_geometry = osmway.geometry
        way_node_list = osmway.node_list

        backward_tags = []
        forward_tags = []
        for tag in segment.osm_tags.keys():
            if "backward" in tag and "forward" in tag:
                if logger.map_logger is not None:
                    logger.map_logger.warning("strange osm tags " + json.dumps(tag))
                continue
            if "backward" in tag:
                backward_tags.append(tag)
            if "forward" in tag:
                forward_tags.append(tag)

        new_osm_tags = deepcopy(segment.osm_tags)
        for tag in forward_tags:
            del new_osm_tags[tag]

        if direction == "backward":
            # reverse the sequence
            segment.geometry = Geometry(way_geometry.lon[::-1], way_geometry.lat[::-1])

            segment.node_list = way_node_list[::-1]
            segment.lane_number = osmway.backward_lanes
            segment.lane_assignment = osmway.backward_lane_assignment
            segment.heading = osmway.backward_heading

            for tag in backward_tags:
                if ":backward" in tag:
                    new_osm_tags[tag.replace(":backward", "")] = segment.osm_tags[tag]
                elif "backward:" in tag:
                    new_osm_tags[tag.replace("backward:", "")] = segment.osm_tags[tag]
                del new_osm_tags[tag]
            segment.osm_tags = new_osm_tags
        else:
            segment.geometry = way_geometry
            segment.node_list = way_node_list
            segment.lane_number = osmway.forward_lanes
            segment.lane_assignment = osmway.forward_lane_assignment
            segment.heading = osmway.forward_heading

            new_osm_tags = deepcopy(segment.osm_tags)
            for tag in backward_tags:
                del new_osm_tags[tag]
            for tag in forward_tags:
                if ":forward" in tag:
                    new_osm_tags[tag.replace(":forward", "")] = segment.osm_tags[tag]
                elif "forward:" in tag:
                    new_osm_tags[tag.replace("forward:", "")] = segment.osm_tags[tag]
                del new_osm_tags[tag]
            segment.osm_tags = new_osm_tags

        segment.osm_tags["lanes"] = str(int(segment.lane_number))
        # shift segment geometry
        if not osmway.directed:
            segment.geometry = \
                shift_geometry(segment.geometry,
                               shift_distance=mapping.DISPLAY_LANE_INTERVAL * mapping.SEGMENT_SHIFT_RATIO,
                               shift_direction="right")

        segment.upstream_node = segment.node_list[0]
        segment.downstream_node = segment.node_list[-1]
        if "direction" in segment.osm_tags.keys():
            segment.from_direction = segment.osm_tags["direction"]
            # segment.from_direction = segment.osm_tags[f"{direction}:direction"]
            # print(segment.from_direction)
        else:
            segment.from_direction = mapping.generate_geo_heading_direction(segment.heading)
        return segment

    def add_downstream_segment(self, seg_id):
        """
        Add an downstream segment if not exists

        :param seg_id: `str`
        :return: `None`
        """
        if not (seg_id in self.downstream_segments):
            self.downstream_segments.append(seg_id)

    def add_upstream_segment(self, seg_id):
        """
        Add an upstream segment if not exists

        :param seg_id: `str`
        :return: `None`
        """
        if not (seg_id in self.upstream_segments):
            self.upstream_segments.append(seg_id)

    def add_laneset(self, laneset):
        self.laneset_list.append(laneset)

    def __str__(self):
        return self.segment_id


def consolidate_segments(network, critical_channels=None):
    """
    consolidate the segments in the same link with the same critical channels

    this function update the entire segment dict and osm_way dict
    fixme: this function should be called before the initiation of the laneset!

    :param network:
    :param critical_channels:
    :return:
    """
    if critical_channels is None:
        critical_channels = ['lane_number', 'speed_limit']

    new_segment_dict = {}
    for link in network.links.values():
        segment_list = link.segment_list
        prv_segment = None

        new_segment_list = []
        consolidated_segment_list = []
        for segment in segment_list:
            if prv_segment is None:
                prv_segment = segment
                consolidated_segment_list = [prv_segment]
                continue
            consolidate_flag = True
            for channel_id in critical_channels:
                if (channel_id in segment.__dict__.keys()) and \
                        (channel_id in prv_segment.__dict__.keys()):
                    cur_seg_attr = getattr(segment, channel_id)
                    prv_seg_attr = getattr(prv_segment, channel_id)
                    if channel_id in ['speed_limit']:
                        if abs(cur_seg_attr - prv_seg_attr) > 0.1:
                            consolidate_flag = False
                            break
                    else:
                        if cur_seg_attr != prv_seg_attr:
                            consolidate_flag = False
                            break

            if consolidate_flag:
                consolidated_segment_list.append(segment)
            else:
                new_segment = merge_segment_list(consolidated_segment_list)
                new_segment_list.append(new_segment)
                new_segment_dict[new_segment.segment_id] = new_segment
                consolidated_segment_list = [segment]
            prv_segment = segment

        # add the last piece of segment group

        new_segment = merge_segment_list(consolidated_segment_list)
        new_segment_list.append(new_segment)
        new_segment_dict[new_segment.segment_id] = new_segment

        link.segment_list = new_segment_list

    network.segments = new_segment_dict
    return network


def merge_segment_list(segment_list):
    if len(segment_list) == 1:
        return segment_list[0]

    osm_way_list = []
    new_node_list = None
    new_length = 0
    new_geometry = None

    for segment in segment_list:
        osm_way_list.append(segment.osm_way)
        new_length += segment.length
        if new_node_list is None:
            new_node_list = segment.node_list
            new_geometry = segment.geometry
            continue
        else:
            new_node_list += segment.node_list[1:]
            new_geometry.append(segment.geometry)

    # set the node within the segment list as ordinary node
    for segment in segment_list[:-1]:
        node = segment.downstream_node
        node.upstream_segments = []
        node.downstream_segments = []
        node.type = NodeCategory.ORDINARY

    segment = segment_list[0]
    # fixme: check the update of the downstream details
    segment.downstream_segments = segment_list[-1].downstream_segments
    segment.downstream_directions_info = segment_list[-1].downstream_directions_info
    node = segment_list[-1].downstream_node
    segment.downstream_node = node
    node.del_upstream_segment(segment_list[-1].segment_id)
    node.upstream_segments.append(segment)
    segment.lane_assignment = segment_list[-1].lane_assignment

    segment.osm_way = osm_way_list
    segment.node_list = new_node_list
    segment.length = new_length
    segment.geometry = new_geometry
    return segment


def generate_network_segments(network):
    """
    initiate the network segment given the osm way each segment is a directed OSM way

    also, initiate the connector node

    :param network:
    :return:
    """
    # create the segment
    for way_id, way in network.ways.items():
        # deal with the back ward and forward separately
        if way.backward_lanes is None:
            # logger.map_logger.warning(way.way_id + " backward direction not initialized correctly!")
            pass
        else:
            # fixme: if the lane number is zero, there must be something wrong with the map data
            #  or the processing, if the lane number is -1, this means that this is a oneway,
            #  the same with the forward direction
            if way.backward_lanes >= 0:
                if way.backward_lanes == 0:
                    if logger.map_logger is not None:
                        logger.map_logger.error(way.way_id, "backward direction lane number equals to 0!")
                backward_segment = Segment.init_from_way(way, "backward")
                network.add_segment(backward_segment)

        if way.forward_lanes is None:
            # logger.map_logger.warning(way.way_id + "forward direction not initialized correctly!")
            pass
        else:
            if way.forward_lanes == 0:
                pass
            forward_segment = Segment.init_from_way(way, "forward")
            network.add_segment(forward_segment)

    for segment_id, segment in network.segments.items():
        if segment.lane_assignment is None:
            # node = network.nodes[segment.downstream_node]
            node = segment.downstream_node
            if not node.is_intersection():
                segment.lane_assignment = "all_through"
            else:
                segment.lane_assignment = "null"

        # add the node upstream and downstream segment
        # network.nodes[segment.upstream_node].downstream_segments.append(segment)
        # network.nodes[segment.downstream_node].upstream_segments.append(segment)
        segment.upstream_node.downstream_segments.append(segment)
        segment.downstream_node.upstream_segments.append(segment)

    # get a special node ---- segment connector
    for node_id, node in network.nodes.items():
        if node.type == NodeCategory.ORDINARY:
            if len(node.upstream_segments) > 0:
                # change this node to connector node
                node.type = NodeCategory.CONNECTOR
                network.nodes.update({node_id: node})
    return network


def generate_segments_connections(network):
    """
    Generate the connections of segments in a network

    :param network: :class:``mtldp.mtlmap.Network``
    :return: :class:``mtldp.mtlmap.Network``
    """
    for node_id, node in network.nodes.items():
        if node.type == NodeCategory.ORDINARY:
            continue
        elif node.type == NodeCategory.CONNECTOR:
            # set the lane assignment to all_through
            upstream_segments = node.upstream_segments
            for segment in upstream_segments:
                # segment = network.segments[upstream_seg]
                if segment.lane_assignment != "all_through":
                    segment.lane_assignment = "all_through"

            if len(node.upstream_segments) == 1:
                upstream_segment = node.upstream_segments[0]
                downstream_segments = node.downstream_segments
                if len(downstream_segments) < 1:
                    if logger.map_logger is not None:
                        logger.map_logger.error("single segment in node " + node_id + ": downstream segments "
                                                + ",".join([str(val) for val in downstream_segments]))
                    continue
                if len(downstream_segments) != 1:
                    if logger.map_logger is not None:
                        logger.map_logger.warning("single segment in node " + node_id + ": downstream segments "
                                                  + ",".join([str(val) for val in downstream_segments]))
                # # add the turning info
                segment = upstream_segment
                segment.downstream_directions_info = {"s": downstream_segments[0]}

                network.add_segment_connection(upstream_segment, downstream_segments[0])
            elif len(node.upstream_segments) == 2:
                upstream_segments = node.upstream_segments
                downstream_segments = node.downstream_segments
                if len(downstream_segments) != 2:
                    if logger.map_logger is not None:
                        logger.map_logger.error("# of downstream segments of segment connector node "
                                                + node_id + "does not equal 2")
                    continue
                up_seg_way_id = []
                for segment in upstream_segments:
                    # segment = network.segments[up_seg]
                    up_seg_way_id.append(segment.osm_way.way_id)
                down_seg_way_id = []
                for segment in downstream_segments:
                    # segment = network.segments[down_seg]
                    down_seg_way_id.append(segment.osm_way.way_id)
                indicator_list = [up_seg_way_id[ii] == down_seg_way_id[jj]
                                  for ii in range(2) for jj in range(2)]

                if indicator_list[0]:
                    network.add_segment_connection(upstream_segments[0], downstream_segments[1])
                    network.add_segment_connection(upstream_segments[1], downstream_segments[0])
                else:
                    # fixme: there might be something wrong here!
                    network.add_segment_connection(upstream_segments[0], downstream_segments[0])
                    network.add_segment_connection(upstream_segments[1], downstream_segments[1])
            else:
                if logger.map_logger is not None:
                    logger.map_logger.error("ordinary node has more than 2 upstream segments ")
        elif node.type == NodeCategory.END:
            upstream_segments = node.upstream_segments
            for segment in upstream_segments:
                # segment = network.segments[upstream_seg]
                if segment.lane_assignment != "all_through":
                    segment.lane_assignment = "all_through"
        elif node.is_intersection():
            upstream_segments = node.upstream_segments
            downstream_segments = node.downstream_segments

            for segment in upstream_segments:
                downstream_directed_segments = {}
                for down_seg in downstream_segments:
                    up_seg_dir = segment.from_direction
                    down_seg_dir = down_seg.from_direction
                    moving_direction = mapping.get_moving_direction(up_seg_dir, down_seg_dir)
                    downstream_directed_segments[moving_direction] = down_seg
                    network.add_segment_connection(segment, down_seg)
                segment.downstream_directions_info = downstream_directed_segments
    return network


def separate_segments_connections(network):
    del_list = []
    new_node_dict = {}
    for node_id, node in network.nodes.items():

        if not node.type == NodeCategory.CONNECTOR:
            continue
        upstream_segments = node.upstream_segments
        downstream_segments = node.downstream_segments

        if len(upstream_segments) != 2 or len(downstream_segments) != 2:
            continue
        flag = '0'

        for upstream_segment in upstream_segments:
            for downstream_segment in downstream_segments:
                if upstream_segment.from_direction == downstream_segment.from_direction:
                    new_node = deepcopy(node)
                    new_node.node_id = node_id + flag
                    new_node.upstream_segments = upstream_segment
                    new_node.downstream_segments = downstream_segment

                    upstream_segment.downstream_node = new_node
                    downstream_segment.upstream_node = new_node
                    new_node_dict[new_node.node_id] = new_node

                    flag = '1'
                    upstream_segment.node_list[-1] = new_node
                    downstream_segment.node_list[0] = new_node
        del_list.append(node_id)

    for del_node in del_list:
        del network.nodes[del_node]
    network.nodes.update(new_node_dict)

    return network