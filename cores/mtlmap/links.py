import numpy as np
import pandas as pd

from ..utils import constants
from ..utils import logger
from .nodes_classes import NodeCategory
from ..utils.geometry import Geometry, get_geometry_from_str


class Link(object):
    """
    A link connects two signalized/unsignalized/origin/destination nodes. It might contain multiple segments


    **Main attributes**
        - ``.link_id`` a integer for link ID. It has the format: number1_number2. The first number is the original node
          of the link. The second number is the destination node of the link.
        - ``.segment_list`` the list of segments that belong to the link
        - ``.geometry`` the GPS coordinates along the link
        - ``.node_list`` a list of nodes on the link
        - ``.upstream_node`` the upstream node of the link
        - ``.downstream_node`` the downstream node of the link
        - ``.heading`` the heading angle of the link (range: (-180,180]))
        - ``.from_direction`` the direction from which the segment originates. For example, if the segment originates
          from south, this value is "S".
        - ``.length`` float, length of the link in meters
    """

    def __init__(self):
        self.link_id = None
        self.segment_list = []
        self.geometry = None
        self.node_list = []
        self.movement_list = []

        self.upstream_node = None
        self.downstream_node = None

        self.heading = None
        self.from_direction = None

        self.speed_limit = None
        self.length = None

        self.dedicated_turn_length = 0  # length of the dedicated lane
        self.stopline_to_center = 0   # distance from stopbar to center of intersection

        # stop bar and clearance time
        self.downstream_stopbar = None
        self.downstream_stopbar_detail = None

        self.upstream_clearance = None
        self.upstream_clearance_detail = None
        # user equilibrium

        self.entry_laneset = None
        self.belonged_arterial = []

    def add_movement(self, movement):
        self.movement_list.append(movement)

    def to_dict(self, attr="all"):
        all_dict = self.__dict__
        link_dict = {}
        if attr == "all":
            link_dict = all_dict.copy()
            attr = all_dict.keys()
        else:
            for one_attr in attr:
                link_dict[one_attr] = all_dict[one_attr]
        for link_attr in {"geometry", "upstream_node", "downstream_node"}.intersection(set(attr)):
            link_dict[link_attr] = str(link_dict[link_attr])
        for link_attr in {"segment_list", "node_list", "buffer_segments", "belonged_arterial"}.intersection(set(attr)):
            link_dict[link_attr] = [str(item) for item in link_dict[link_attr]]

        return link_dict

    def to_df(self, attr="all"):
        link_dict = self.to_dict(attr=attr)
        return pd.DataFrame(link_dict, index=[0])

    def __str__(self):
        return self.link_id


def get_link_from_dict(input_link_dict):
    link = Link()
    link.__dict__ = input_link_dict.copy()
    link.__dict__["geometry"] = get_geometry_from_str(input_link_dict["geometry"])
    return link


def generate_network_links(network):
    """
    generate network links
    combine the segment to get the link, start from each intersection node and end node
    connects the segment until encounter next end node or intersection node

    :param network: `mtldp.mtlmap.Network`
    :return: `mtldp.mtlmap.Network` with links added
    """
    for node_id, node in network.nodes.items():
        if node.type == NodeCategory.ORDINARY or node.type == NodeCategory.CONNECTOR:
            continue
        downstream_segments = node.downstream_segments
        for segment in downstream_segments:
            segment_list = [segment]
            # segment = network.segments[segment_id]

            maximum_loops = 20
            loop_count = 0
            while True:
                loop_count += 1
                if loop_count > maximum_loops:
                    break

                downstream_node = segment.downstream_node
                if downstream_node.type == NodeCategory.ORDINARY:
                    if logger.map_logger is not None:
                        logger.map_logger.error("something wrong here, "
                                                "downstream node of a segment is "
                                                "ordinary node")
                        logger.map_logger.error("segment id" + segment.segment_id +
                                                "downstream node" + segment.downstream_node.node_id)

                # jump out of the loop if the downstream node is not an ordinary node
                if downstream_node.type != NodeCategory.CONNECTOR:
                    break
                local_down_segs = segment.downstream_segments
                if len(local_down_segs) != 1:
                    if logger.map_logger is not None:
                        logger.map_logger.error("the # of downstream segments at the ordinary connector"
                                                " is not 1")
                        logger.map_logger.error("segment id " + segment.segment_id +
                                                " downstream segs: " +
                                                " ".join([str(val.segment_id) for val in segment.downstream_segments]))
                    continue

                # down_seg_id = local_down_segs[0]
                # segment = network.segments[down_seg_id]
                segment = local_down_segs[0]
                segment_list.append(segment)

            # detect repeat
            if len(set(segment_list)) != len(segment_list):
                if logger.map_logger is not None:
                    logger.map_logger.error("circle segments in link generation")
                    logger.map_logger.error("details: " + ",".join([str(val) for val in segment_list]))

            # print([seg.segment_id for seg in segment_list])
            link = generate_link_from_segments(segment_list)
            network.add_link(link, repeat_add_name='r')

    # update laneset info
    for laneset_id, laneset in network.lanesets.items():
        segment_id = laneset.belonged_segment
        segment = network.segments[segment_id]

        laneset.belonged_link = segment.belonged_link
        laneset.speed_limit = segment.speed_limit
        laneset.upstream_node = segment.upstream_node
        laneset.downstream_node = segment.downstream_node
    return network


def generate_link_details(network):
    """
    Generate the details of the links in a network
    Update the links after determining the laneset

    to determine the:
    1) dedicated_turn_length
    2) entry_laneset

    :param network: `mtldp.mtlmap.Network`
    :return: `mtldp.mtlmap.Network`
    """
    for link_id, link in network.links.items():
        segment_list = link.segment_list
        length_before_turn = 0
        for segment in segment_list:
            laneset_list = segment.laneset_list
            if len(laneset_list) > 0:
                break
            length_before_turn += segment.length
        link.dedicated_turn_length = link.length - length_before_turn

        segment = segment_list[0]
        laneset_list = segment.laneset_list
        if len(laneset_list) > 1:
            if logger.map_logger is not None:
                logger.map_logger.warn(f"Link {link} have multiple entry lanesets, choose one of them.")
        link.entry_laneset = laneset_list[0]
    return network


def generate_link_from_segments(segment_list):
    """
    Generate the link and add the link to the network given a series of segments

    :param segment_list: the list of the segment id
    :return: `mtldp.mtlmap.Link`
    """
    link = Link()
    link.segment_list = segment_list
    # segment = network.segments[segment_list[0]]
    segment = segment_list[0]
    upstream_node = segment.upstream_node
    link.upstream_node = upstream_node

    lat_list = [segment.geometry.lat[0]]
    lon_list = [segment.geometry.lon[0]]

    # segment = network.segments[segment_list[-1]]
    segment = segment_list[-1]
    downstream_node = segment.downstream_node
    link.downstream_node = downstream_node

    link.link_id = upstream_node.node_id + "_" + downstream_node.node_id
    upstream_node.downstream_links.append(link)
    downstream_node.upstream_links.append(link)

    # add link id to the segment
    node_list = [upstream_node]

    heading_list = []
    total_length = 0
    total_free_travel_time = 0
    for segment in segment_list:
        segment.belonged_link = link
        # segment = network.segments[segment_id]
        total_length += segment.length
        seg_free_v = segment.speed_limit
        if seg_free_v is None or seg_free_v <= 0:
            seg_free_v = 12
        total_free_travel_time += segment.length / seg_free_v

        heading_list.append(segment.heading)
        segment_geometry = segment.geometry
        segment_nodes = segment.node_list
        node_list += segment_nodes[1:]
        lat_list += segment_geometry.lat[1:]
        lon_list += segment_geometry.lon[1:]

    link.speed_limit = total_length / total_free_travel_time
    link.length = total_length
    link.node_list = node_list
    link.geometry = Geometry(lon_list, lat_list)
    link.heading = np.average(heading_list)
    link.from_direction = constants.generate_geo_heading_direction(link.heading)
    return link


if __name__ == "__main__":
    import mtldp.mtlmap as mtlmap

    net = \
        mtlmap.build_network_from_xml("test",
                                      "/Users/zhangchenhao/Desktop/New-versions/mtl-data-platform/data/birmingham.osm")
    l = net.links["61841928_61841935"]
    d = l.to_dict()
    ll = get_link_from_dict(d)
    print()

    # cnt = True
    # for k, v in n.__dict__.items():
    #     if v != n2.__dict__[k]:
    #         print("H")
    #         cnt = False
    # print(cnt)
