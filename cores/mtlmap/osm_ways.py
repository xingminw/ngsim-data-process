from ..utils import logger
from ..utils import constants as utils
from ..utils.gps_utils import get_trace_length, get_gps_trace_heading_info
from ..utils.geometry import Geometry


class OsmWay(object):
    """
    OsmWay corresponds to the "way" in the original osm data

    **Main attributes**
        - ``.osm_tags`` a dictionary contains all the tags in the original osm data.
        - ``.osm_attrib`` a dictionary contains all the attributes in the original osm data.
        - ``.way_id`` a integer for OSM way ID
        - ``.node_list`` a list of nodes on the way
        - ``.length`` length of the way in meters
        - ``.geometry`` the GPS coordinates along the way
        - ``.forward_heading`` the heading angle at the start of the way (range: (-180,180]))
        - ``.backward_heading`` the heading angle at the end of the way (range: (-180,180]))
        - ``.lane_number`` number of lanes
        - ``.forward_lanes`` number of lanes from the start of the way to the end of the way
        - ``.backward_lanes`` number of lanes from the end of the way to the start of the way
        - ``.name`` name of the way
        - ``.speed_limit`` speed limit of the way in m/s

    """

    def __init__(self, way_id: str = None, node_list=None,
                 osm_attrib=None, osm_tags=None):
        # original info from osm (xml) data
        self.osm_tags = osm_tags
        self.osm_attrib = osm_attrib

        self.way_id = way_id

        self.node_list = node_list
        # self.lane_sets = {}
        # self.lanes = {}

        self.length = None                  # unit: meters
        self.geometry = None                # mtldp.utils.Geometry
        self.forward_heading = None
        self.weighted_forward_heading = None
        self.backward_heading = None
        self.weighted_backward_heading = None

        self.lane_number = None        # fixme:

        self.forward_lanes = None
        self.backward_lanes = None

        self.forward_lane_assignment = None
        self.backward_lane_assignment = None

        self.directed = False       # fixme: I think all the ways are undirected.
        self.name = None
        self.speed_limit = None

        if (self.way_id is not None) and (self.osm_attrib is not None) and (self.osm_tags is not None):
            self.generate_basic_info()

    def generate_basic_info(self):
        """
        extract useful information from the osm attrib and tags

        current extracted information includes:
            - oneway or not
            - lane information (# and assignment)
            - speed limit (25mph if null)
            - name

        :return:
        """
        if "maxspeed" in self.osm_tags.keys():
            speed_limit = self.osm_tags["maxspeed"]
        else:
            if "maxspeed:forward" in self.osm_tags.keys():
                speed_limit = self.osm_tags["maxspeed:forward"]
            else:
                speed_limit = "25 mph"

        speed = float(speed_limit.split(" ")[0])
        self.speed_limit = speed * utils.MPH_TO_METERS_PER_SEC
        if "oneway" in self.osm_tags.keys():
            if self.osm_tags["oneway"] == "yes":
                self.directed = True
                # fixme: here the backward lane must be -1,
                #  see function generating the segments of the network for details
                self.backward_lanes = -1
            else:
                self.directed = False
        else:
            self.directed = False

        if "name" in self.osm_tags.keys():
            self.name = self.osm_tags["name"]
        else:
            self.name = "null"

        # load lane number and lane assignment
        if "lanes" in self.osm_tags.keys():
            self.lane_number = int(self.osm_tags["lanes"])

            if "lanes:backward" in self.osm_tags.keys():
                self.backward_lanes = int(self.osm_tags["lanes:backward"])
            if "lanes:forward" in self.osm_tags.keys():
                self.forward_lanes = int(self.osm_tags["lanes:forward"])

            if self.directed:
                self.forward_lanes = self.lane_number
            else:
                if self.backward_lanes is None and self.forward_lanes is None:
                    self.forward_lanes = self.lane_number / 2
                    self.backward_lanes = self.lane_number / 2
                if self.backward_lanes is None:
                    self.backward_lanes = self.lane_number - self.forward_lanes
                if self.forward_lanes is None:
                    self.forward_lanes = self.lane_number - self.backward_lanes

            if "turn:lanes" in self.osm_tags.keys():
                self.forward_lane_assignment = self.osm_tags["turn:lanes"]
            if "turn:lanes:backward" in self.osm_tags.keys():
                self.backward_lane_assignment = self.osm_tags["turn:lanes:backward"]
            if "turn:lanes:forward" in self.osm_tags.keys():
                self.forward_lane_assignment = self.osm_tags["turn:lanes:forward"]
        else:
            self.forward_lanes = 1
            self.backward_lanes = 1
            if "oneway" in self.osm_tags.keys():
                if self.osm_tags["oneway"] == "yes":
                    self.directed = True
                    # fixme: here the backward lane must be -1,
                    #  see function generating the segments of the network for details
                    self.backward_lanes = -1
            if logger.map_logger is not None:
                logger.map_logger.warning(self.way_id + " does not have lane number!")

        self.forward_lanes = int(self.forward_lanes)
        self.backward_lanes = int(self.backward_lanes)

    def update_way_geometry(self):
        """
        Update the geometric information of a link

        :return: None
        """
        node_list = self.node_list

        latitude_list = []
        longitude_list = []
        for node in node_list:
            # node = network.nodes[node_id]
            latitude_list.append(node.latitude)
            longitude_list.append(node.longitude)
        self.geometry = Geometry(longitude_list, latitude_list)
        self.length = get_trace_length(latitude_list, longitude_list)
        heading_info = get_gps_trace_heading_info(latitude_list, longitude_list)
        self.forward_heading = heading_info[0]
        self.weighted_forward_heading = heading_info[1]
        self.backward_heading = heading_info[2]
        self.weighted_backward_heading = heading_info[3]

    def __str__(self):
        return self.way_id


def parse_osm_ways(network):
    """
    parse the node and way of the osm data
    extract useful information from osm data to the python object

    Add the following attributes of Node
        - od_segments
        - traverse_segments

    Add the following attributes of OsmWay
        - length and geometry
        - directed or not
        - lane information (# and assignment)

    This function also:
        - Remove way that does not have less than two nodes
        - Remove node that does not belong to any way

    :param network: `mtldp.mtlmap.Network`
    :return: `mtldp.mtlmap.Network`
    """
    useful_nodes = []
    deleted_ways = []

    # update the geometry of the way
    for way_id, way in network.ways.items():
        # update the way geometry
        update_way_geometry(network, way_id)

        node_list = way.node_list
        # get the useful nodes
        for node_id in node_list:
            if not (node_id in useful_nodes):
                useful_nodes.append(node_id)

        # check whether the node belongs to the network
        valid_node_list = []
        for node_id in node_list:
            if not (node_id in network.nodes.keys()):
                if logger.map_logger is not None:
                    logger.map_logger.warning("Node id " + node_id + " in " + way_id + "not in the map!")
            else:
                valid_node_list.append(node_id)

        node_list = valid_node_list
        if len(node_list) <= 1:
            if logger.map_logger is not None:
                logger.map_logger.warning(way_id + " does not have node (delete this way then)")
            deleted_ways.append(way_id)
            continue

        # update the od_segments and traverse segments of each node
        od_nodes = [node_list[0], node_list[-1]]
        traverse_nodes = node_list[1:-1]
        for od_node in od_nodes:
            node = network.nodes[od_node]
            node.od_ways.append(way_id)

        for traverse_n in traverse_nodes:
            node = network.nodes[traverse_n]
            node.traverse_ways.append(way_id)

    # delete way without nodes
    for way_id in deleted_ways:
        del network.ways[way_id]

    # reconstruct the node dict (remove useless nodes)
    new_node_dict = {}
    for node_id in network.nodes.keys():
        if node_id in useful_nodes:
            new_node_dict[node_id] = network.nodes[node_id]
    network.nodes = new_node_dict
    return network


def fetch_node_for_ways(network):
    """
    Change the node list of osm ways to the node according to the node id

    :param network: `mtldp.mtlmap.Network`
    :return: `mtldp.mtlmap.Network`
    """
    for way_id, way in network.ways.items():
        node_list = way.node_list
        new_node_list = []
        for node_id in node_list:
            new_node_list.append(network.nodes[node_id])
        way.node_list = new_node_list
    return network


def update_way_geometry(network, way_id):
    """
    Update the geometric information of a given way in a network

    :param network: `mtldp.mtlmap.Network`
    :param way_id: str
    :return:
    """
    way = network.ways[way_id]
    node_list = way.node_list

    latitude_list = []
    longitude_list = []
    for node_id in node_list:
        if not (node_id in network.nodes.keys()):
            if logger.map_logger is not None:
                logger.map_logger.warning("cannot find node " + node_id + " in way " + way_id)
            continue
        node = network.nodes[node_id]
        latitude_list.append(node.latitude)
        longitude_list.append(node.longitude)
    way.geometry = Geometry(longitude_list, latitude_list)
    way.length = get_trace_length(latitude_list, longitude_list)
    heading_info = get_gps_trace_heading_info(latitude_list, longitude_list)
    way.forward_heading = heading_info[0]
    way.weighted_forward_heading = heading_info[1]
    way.backward_heading = heading_info[2]
    way.weighted_backward_heading = heading_info[3]
