from ..utils import constants
from ..utils import logger
from ..utils.gps_utils import shift_geometry
from .nodes_classes import NodeCategory


class LaneSet(object):
    def __init__(self):
        self.laneset_id = None

        # segment id of this pipeline
        self.belonged_segment = None
        self.belonged_link = None

        self.length = None  # unit: meters
        self.speed_limit = None  # unit: meters / sec
        self.lane_number = None

        # "l", "r", "s", "lrs", "sr", etc. (left, right, straight, and combination)
        self.turn_direction = None
        self.movement_dict = {}

        # offset: 0 through   1 left   -1 right
        self.geometry_offset = None
        self.geometry = None

        # connection with other elements
        self.upstream_node = None
        self.downstream_node = None

        # upstream and downstream connector
        self.downstream_laneset_list = []
        self.upstream_laneset_list = []

    @classmethod
    def init_from_segment(cls, segment, movement_dict,
                          lane_number, insegment_offset):
        """
        Initialize laneset from the input segment

        :param segment: `mtldp.mtlmap.Segment`
        :param movement_dict: dict of movement, key: "s", "l", val: movement
        :param lane_number: int
        :param insegment_offset: int
        :return: `mtldp.mtlmap.Laneset`
        """
        laneset = cls()
        laneset.lane_number = lane_number
        laneset.turn_direction = ''.join(list(movement_dict.keys()))
        laneset.movement_dict = movement_dict
        laneset.laneset_id = segment.segment_id + "_" + str(insegment_offset)
        laneset.belonged_segment = segment
        laneset.belonged_link = segment.belonged_link
        laneset.speed_limit = segment.speed_limit
        laneset.upstream_node = segment.upstream_node
        laneset.downstream_node = segment.downstream_node

        if insegment_offset > 0:
            laneset.geometry = shift_geometry(segment.geometry,
                                              shift_distance=constants.DISPLAY_LANE_INTERVAL,
                                              shift_direction="left")
        elif insegment_offset == 0:
            laneset.geometry = segment.geometry
        else:
            laneset.geometry = shift_geometry(segment.geometry,
                                              shift_distance=constants.DISPLAY_LANE_INTERVAL,
                                              shift_direction="right")
        laneset.length = segment.length
        laneset.geometry_offset = insegment_offset

        # add this laneset also to the segment
        segment.add_laneset(laneset)
        return laneset

    def __str__(self):
        return self.laneset_id


def _get_movement_dict(movement_list):
    movement_dict = {}
    for movement in movement_list:
        movement_dict[movement.direction] = movement
    return movement_dict


def generate_network_lanesets(network):
    """
    Laneset is generated from each segment according to the lane assignment

    :param network:
    :return:
    """
    for segment in network.segments.values():
        node = segment.downstream_node
        if node.is_intersection():
            # if downstream node is an intersection, there might be some dedicated-turning laneset
            lane_assignment = segment.lane_assignment
            link = segment.belonged_link
            movement_list = link.movement_list
            movement_dict = _get_movement_dict(movement_list)

            # get the number for dedicated turning lanesets
            total_lane_number = segment.lane_number
            left_lane_number = 0
            right_lane_number = 0
            if lane_assignment is not None:
                lane_assign_list = lane_assignment.split('|')
                for td in lane_assign_list:
                    if td == 'left':
                        left_lane_number += 1
                    elif td == right_lane_number:
                        right_lane_number += 1
            through_lane_number = total_lane_number - left_lane_number - right_lane_number
            if through_lane_number == total_lane_number:
                # all the direction are mixed together
                laneset = LaneSet().init_from_segment(segment, movement_dict, total_lane_number, 0)
                network.lanesets[laneset.laneset_id] = laneset
            else:
                # dedicated left-turn laneset
                if left_lane_number > 0:
                    if 'l' in movement_dict:
                        laneset = LaneSet().init_from_segment(segment,
                                                              {'l': movement_dict['l']},
                                                              left_lane_number, 1)
                        network.lanesets[laneset.laneset_id] = laneset
                        del movement_dict['l']
                    else:
                        if logger.map_logger is not None:
                            logger.map_logger.error(f'Left movement missing in link {link}')

                if right_lane_number > 0:
                    if 'r' in movement_dict:
                        laneset = LaneSet().init_from_segment(segment,
                                                              {'r': movement_dict['r']},
                                                              right_lane_number, -1)
                        network.lanesets[laneset.laneset_id] = laneset
                        del movement_dict['r']
                    else:
                        if logger.map_logger is not None:
                            logger.map_logger.error(f'Left movement missing in link {link}')

                if through_lane_number > 0:
                    laneset = LaneSet().init_from_segment(segment,
                                                          movement_dict,
                                                          through_lane_number, 0)
                    network.lanesets[laneset.laneset_id] = laneset
        else:
            # if the downstream node is not an intersection, this segment only has one laneset
            laneset = LaneSet().init_from_segment(segment, {},
                                                  segment.lane_number, 0)
            network.lanesets[laneset.laneset_id] = laneset
    return network


def generate_laneset_connections(network):
    for node_id, node in network.nodes.items():
        if node.is_intersection():
            upstream_segments = node.upstream_segments
            for segment in upstream_segments:
                downstream_dirs = segment.downstream_directions_info

                lanesets_list = segment.laneset_list
                for laneset in lanesets_list:
                    directions = list(laneset.turn_direction)

                    direction_list = []
                    segment_list = []

                    for direction in directions:
                        # ignore the backward connection
                        if direction == 'b':
                            continue

                        if not (direction in downstream_dirs.keys()):
                            logger.map_logger.warning("downstream_dirs does not have direction " + direction +
                                                      " in segment " + segment.segment_id)
                            continue

                        if downstream_dirs[direction] is None:
                            logger.map_logger.warning("downstream direction " + direction +
                                                      " not found of laneset " + laneset.laneset_id)
                        else:
                            direction_list.append(direction)
                            segment_list.append(downstream_dirs[direction])
                    for downstream_segment in segment_list:
                        if len(downstream_segment.laneset_list) != 1:
                            continue
                        downstream_laneset = downstream_segment.laneset_list[0]
                        laneset.downstream_laneset_list.append(downstream_laneset)
                        downstream_laneset.upstream_laneset_list.append(laneset)
        if node.type == NodeCategory.CONNECTOR:
            upstream_segment = node.upstream_segments
            downstream_segment = node.downstream_segments
            for upstream_laneset in upstream_segment.laneset_list:
                for downstream_laneset in downstream_segment.laneset_list:
                    upstream_laneset.downstream_laneset_list.append(downstream_laneset)
                    downstream_laneset.upstream_laneset_list.append(upstream_laneset)
    return network
