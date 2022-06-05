import numpy as np

from ..utils import constants
from ..utils import logger
from ..utils.gps_utils import shift_geometry


class LaneSet(object):
    """
    LaneSet is a set of lanes that has the same downstream direction (e.g. through movement, left turn, right turn).
     It can be used to build CTM or LTM model.

    **Main attributes**
        - ``.laneset_id`` a integer for laneset ID. The lane set index within the segment is added to the segment ID.
          For example, if the segment ID is 1768090910, and the laneset index is 0, this value should be "1768090910_0"
        - ``.type`` type of the road. Could be "internal", "source", or "destination"
        - ``.belonged_segment`` the segment ID that this lane set belongs to
        - ``.belonged_link`` the link ID that this lane set belongs to
        - ``.turning_direction`` the movement of this lane set. For example, 's' means through movement (straight).
          'r' means right turn movement, and 'l' means left turn movement. The value can also be the combination of
          's', 'r' and 'l'
        - ``.length`` length of the lane set in meters
        - ``.speed_limit`` speed limit of the lane set in m/s
        - ``.lane_number`` number of lanes of the lane sets
        - ``.heading`` the heading angle of the lane sets (range: (-180,180]))
        - ``.from_direction`` the direction from which the lane set originates. For example, if the lane set originates
          from south, this value is "S".
        - ``.geometry`` the GPS coordinates along the lane set
        - ``.downstream_lanesets`` the downstream lane sets that it connects to
        - ``.turning_ratio_list`` the list of turning ratio information. The value is None if unavailable
        - ``.upstream_node`` the upstream node of the lane set
        - ``.downstream_node`` the downstream node of the lane set
        - ``.phase_id`` the ID of the phase associated with the lane set
    """

    def __init__(self):
        self.laneset_id = None
        self.type = None  # "internal", "source", "destination"

        # segment id of this pipeline
        self.belonged_segment = None
        self.belonged_link = None
        self.lane_list = []

        self.turning_direction = None  # "l", "r", "s", or their combination
        self.length = None  # unit: meters
        self.speed_limit = None  # unit: meters / sec
        self.lane_number = None

        self.heading = None
        self.from_direction = None

        self.downstream_connector = None
        self.upstream_connectors = []
        self.geometry = None

        # offset: 0 - through   1 - left   -1  -  right
        self.insegment_offset = None  # fixme

        self.downstream_lanesets = []  # downstream pipeline id list
        self.turning_ratio_list = None  # turning ratio list

        self.upstream_node = None
        self.downstream_node = None

        # traffic signal attributes
        self.phase_id = None
        self.movement_list = []  # fixme: what is the difference between movement_list and turning_direction

        self.travel_time = None
        self.free_travel_time = None
        self.capacity = None
        self.belonged_path = []
        self.laneset_flow = None

        # user equilibrium
        self.laneset_previous_flow = None

    @classmethod
    def init_from_segment(cls, segment, direction,
                          lane_number, insegment_offset):
        """
        Initialize laneset from the input segment

        :param segment: `cores.mtlmap.Segment`
        :param direction: str
        :param lane_number: int
        :param insegment_offset: int
        :return: `cores.mtlmap.Laneset`
        """
        laneset = cls()
        laneset.lane_number = lane_number
        laneset.turning_direction = direction
        laneset.laneset_id = segment.segment_id + "_" + str(insegment_offset)
        laneset.belonged_segment = segment
        laneset.belonged_link = segment.belonged_link
        laneset.speed_limit = segment.speed_limit
        laneset.upstream_node = segment.upstream_node
        laneset.from_direction = segment.from_direction
        laneset.heading = segment.heading
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
        laneset.insegment_offset = insegment_offset
        laneset.free_travel_time = laneset.length / laneset.speed_limit
        laneset.capacity = laneset.lane_number * 1800
        return laneset

    def compute_travel_time(self):
        """
        Compute the travel time according to the link performance function

        :return: None
        """
        self.travel_time = self.free_travel_time * (1 + 0.15 * pow(self.laneset_flow / self.capacity, 4))

    def compute_cumulative_travel_time(self, alpha):
        """
        Objective function of the BPR link performance function

        :param alpha: float
        :return: float
        """
        current_flow = self.laneset_previous_flow + alpha * (self.laneset_flow - self.laneset_previous_flow)
        objective_function = self.free_travel_time * current_flow + 0.15 / 5 * self.free_travel_time * \
                             pow(current_flow / self.capacity, 5) * self.capacity
        return objective_function

    def update_current_flow(self, flow):
        self.laneset_flow = flow

    def update_previous_flow(self):
        self.laneset_previous_flow = self.laneset_flow

    def update_belonged_paths(self, path_id):
        if path_id not in self.belonged_path:
            self.belonged_path.append(path_id)

    # def to_dict(self, attr="all"):
    #     all_dict = self.__dict__
    #     laneset_dict = {}
    #     if attr == "all":
    #         laneset_dict = all_dict.copy()
    #         attr = all_dict.keys()
    #     else:
    #         for one_attr in attr:
    #             laneset_dict[one_attr] = all_dict[laneset_dict]
    #
    #     for one_attr in {"belonged_segment", "belonged_link", "downstream_connector", "upstream_connectors", "geometry",
    #                      "upstream_node", "downstream_node"}.intersection(set(attr)):
    #         if all_dict[one_attr] is not None:
    #             laneset_dict[one_attr] = str(laneset_dict[one_attr])
    #     for one_attr in {"lane_list", "downstream_lanesets", "movement_list", "belonged_path"}.intersection(set(attr)):
    #         laneset_dict[one_attr] = [str(item) for item in laneset_dict[one_attr]]
    #
    #     return laneset_dict

    def __str__(self):
        return self.laneset_id


class Lane(object):
    """
    This class is not used yet, usually we do not need the lane
    """
    def __init__(self, lane_id):
        """

        :param lane_id:
        """
        self.lane_id = lane_id
        # store the lane index, starting from 0 (right)
        self.index = None
        self.segment = None
        self.speed_limit = None
        self.length = None
        self.geometry = None
        self.downstream_node = None
        self.upstream_node = None
        self.controlled_movement = None
        self.downstream_connectors = []
        self.upstream_connectors = []

        self.upstream_lanes = []
        self.downstream_lanes = []
        self.belonged_laneset = None

    def __str__(self):
        return self.lane_id


def generate_network_lanesets(network):
    """

    :param network:
    :return:
    """
    for node_id, node in network.nodes.items():
        if node.type == "ordinary":
            continue
        elif node.type == "connector" or node.type == "end":
            upstream_segments = node.upstream_segments
            for segment in upstream_segments:
                # segment = network.segments[upstream_seg]
                lanesets = segment.generate_lanesets()
                for laneset in lanesets:
                    network.add_laneset(laneset)

        elif node.is_intersection():
            upstream_segments = node.upstream_segments
            for segment in upstream_segments:
                # segment = network.segments[up_seg]
                # todo: I need to change here
                downstream_directed_segments = segment.downstream_directions_info
                overall_directions = ""
                for dir_k, dir_v in downstream_directed_segments.items():
                    if dir_v in overall_directions:
                        continue
                    else:
                        overall_directions += dir_v
                segment_lane_number = int(segment.lane_number)
                if segment.lane_assignment == "null":
                    assignments = None
                    if segment_lane_number == 0:
                        if logger.map_logger is not None:
                            logger.map_logger.warning("segment " + segment.segment_id + " lane number equals 0.")
                    elif segment_lane_number == 1:
                        assignments = [{"dir": overall_directions, "num": segment_lane_number, "shift": 0}]
                    else:
                        if "s" in overall_directions:
                            left_lanes = segment_lane_number
                            assignments = []
                            if "l" in overall_directions:
                                assignments.append({"dir": "l", "num": 1, "shift": 1})
                                left_lanes -= 1

                            if "r" in overall_directions:
                                if left_lanes > 2:
                                    assignments.append({"dir": "r", "num": 1, "shift": -1})
                                    assignments.append({"dir": "s", "num": left_lanes - 1, "shift": 0})
                                else:
                                    assignments.append({"dir": "rs", "num": left_lanes, "shift": 0})
                            else:
                                assignments.append({"dir": "s", "num": left_lanes, "shift": 0})
                        else:
                            if len(overall_directions) == 1:
                                assignments = [{"dir": overall_directions, "num": segment_lane_number, "shift": 0}]
                            else:
                                left_lanes = int(np.ceil(segment_lane_number / 2))
                                assignments = [{"dir": "l", "num": left_lanes, "shift": 1},
                                               {"dir": "r", "num": segment_lane_number - left_lanes, "shift": 0}]
                    lanesets = segment.generate_lanesets(assignments)
                    for laneset in lanesets:
                        network.add_laneset(laneset)
                elif segment.lane_assignment == "|":
                    assignments = [{"dir": overall_directions, "num": segment_lane_number, "shift": 0}]
                    lanesets = segment.generate_lanesets(assignments)
                    for laneset in lanesets:
                        network.add_laneset(laneset)
                else:
                    if "left" in segment.lane_assignment:
                        if not ("l" in overall_directions):
                            if logger.map_logger is not None:
                                logger.map_logger.error("left downstream of segment " +
                                                        segment.segment_id + " segment not detected. ")
                    if "right" in segment.lane_assignment:
                        if not ("r" in overall_directions):
                            if logger.map_logger is not None:
                                logger.map_logger.error("right downstream of segment " +
                                                        segment.segment_id + " segment not detected. ")
                                logger.map_logger.error("lane assignment " + segment.lane_assignment +
                                                        "detected direction: " +
                                                        ",".join(segment.downstream_directions_info.keys()))
                    if not ("left|right" in segment.lane_assignment):
                        if not ("left" == segment.lane_assignment):
                            if not ("right" == segment.lane_assignment):
                                if not ("s" in overall_directions):
                                    if logger.map_logger is not None:
                                        logger.map_logger.error("straight downstream of segment " +
                                                                segment.segment_id + " segment not detected")
                    lanesets = segment.generate_lanesets()
                    for laneset in lanesets:
                        network.add_laneset(laneset)

    # update the upstream/downstream lanesets
    for laneset_id, laneset in network.lanesets.items():
        node = laneset.upstream_node
        # node = network.nodes[upstream_node]
        node.downstream_lanesets.append(laneset)
        node = laneset.downstream_node
        # node = network.nodes[downstream_node]
        node.upstream_lanesets.append(laneset)
    return network
