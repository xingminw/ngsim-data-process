"""
This file is to process the map data and construct the network class

The map data processing includes the following procedure:

"""

import os

from .map_modes import MapMode
from .map_xml import load_xml_map
from .map_process import split_traverse_intersection_way
from .map_json import overwrite_map_attributes
from .nodes_classes import node_differentiation, infer_node_name
from .osm_ways import parse_osm_ways, fetch_node_for_ways
from .segments import generate_network_segments, \
    generate_segments_connections, consolidate_segments,\
    separate_segments_connections
from .links import generate_network_links, generate_link_details
from .movements import generate_network_movements, generate_movement_details
from .laneset import generate_network_lanesets, generate_laneset_connections
from .connections import generate_network_connectors


from ..utils import logger


def build_network_from_xml(region_name: str,
                           file_name: str, city_id='', logger_path: str = "output", logger_file="map.log",
                           mode: "mtldp.mtlmap.MapMode" = MapMode.ACCURATE,
                           build_networkx: bool = True, intersection_name_file: str = None,
                           overwrite_json: str = None):
    """
    Build the network class in :py:class:`mtldp.mtlmap.Network` from OpenStreetMap data

    :param region_name: region name of the network
    :param intersection_name_file: str, name of the file that containing the name of the intersections
    :param file_name: str, input map file name (`.osm` or `.xml`)
    :param city_id: str, default ''
    :param build_networkx: bool, whether build the networkx graph object (Default: True)
    :param logger_path: str, output logger path, name as `/map.log`
    :param logger_file: str, name of the logger file
    :param mode: `mtldp.mtlmap.MapMode`, mode selection for the network layers
    :param overwrite_json: overwrite json file

    :return: Static network class :py:class:`mtldp.mtlmap.Network`,
             see :ref:`reference <static_core>` for the list of the static network classes
    """
    if not os.path.exists(logger_path):
        os.makedirs(logger_path)

    # create the logger to record the map data processing process
    if logger_file is not None:
        logger_file = logger_path + f"/{logger_file}"
        if os.path.exists(logger_file):
            os.remove(logger_file)

        logger.map_logger = logger.setup_logger("map-data", logger.map_logger_formatter, logger_file)

        logger.map_logger.info("Loading the map data from " + file_name + " ...")
        logger.map_logger.info("Process the map data using " + mode.name + " mode...")

    # parse osm way and node
    network = load_xml_map(region_name, file_name, city_id=city_id)

    # parse the node and way in the original osm data
    if logger_file is not None:
        logger.map_logger.info("Parsing the original osm data...")

    # differentiate vertex node and traverse node of way
    network = parse_osm_ways(network)
    network.reset_bound()

    # node differentiation
    if logger_file is not None:
        logger.map_logger.info("Differentiate the node...")
    network = node_differentiation(network)
    network = fetch_node_for_ways(network)

    # split the way that traverses the intersections
    if logger_file is not None:
        logger.map_logger.info("Split osm ways that traverse the intersections...")
    network = split_traverse_intersection_way(network)
    # update the node index for the osm way since the nodes have been changed

    # create network segment
    if logger_file is not None:
        logger.map_logger.info("Generating the segments...")

    # build directed segments and connectors
    network = generate_network_segments(network)
    # network = update_node_index(network)

    if build_networkx:
        if logger_file is not None:
            logger.map_logger.info("Build networkx graph...")
        network.build_networkx_graph()

    if mode == MapMode.MAP_MATCHING:
        if logger_file is not None:
            logger.map_logger.info("Map data processing done. (MAP_MATCHING MODE)")
        return network

    if logger_file is not None:
        logger.map_logger.info("Generate segment connections...")
    network = generate_segments_connections(network)

    if logger_file is not None:
        logger.map_logger.info("separate segments connections...")
    network = separate_segments_connections(network)

    # create network links
    if logger_file is not None:
        logger.map_logger.info("Generating the network links...")
    network = generate_network_links(network)

    if logger_file is not None:
        logger.map_logger.info("Generating the network movements...")
    network = generate_network_movements(network)

    # consolidate segments
    if logger_file is not None:
        logger.map_logger.info("Consolidate segments...")
    network = consolidate_segments(network)



    # logger.map_logger.info("Adding stop bar and clearance point...")
    # network = identify_stopbar_clearance(network)

    network = _load_intersection_name(network, intersection_name_file)
    network = infer_node_name(network)

    if overwrite_json is not None:
        if os.path.exists(overwrite_json):
            network = overwrite_map_attributes(network, overwrite_json)
            if logger_file is not None:
                logger.map_logger.info("Loading the overwrite json file done.")
        else:
            if logger_file is not None:
                logger.map_logger.warning("Overwrite json file not detected")

    if mode == MapMode.MOVEMENT:
        if logger_file is not None:
            logger.map_logger.info("Map data processing done. (ROUGH_MAP MODE)")
        return network

    # Todo: note that overwrite is before the laneset initiation,
    #  three important parts that are required to check after the overwrite here:
    #  1) Lane number: should be corrected in the raw osm file
    #  2) Lane usage (turn): should be corrected in the raw osm file
    #  3) Movement index:
    #  other useful but optional process
    #  a) stopline location for the mobility purpose (not  enough for safety applications, e.g., red light running)
    #  b)

    # generate the connection of the lane sets and segments at intersections
    if logger_file is not None:
        logger.map_logger.info("Generating the lanesets...")
    network = generate_network_lanesets(network)

    if logger_file is not None:
        logger.map_logger.info("Generating the lanesets connections...")
    network = generate_laneset_connections(network)

    if logger_file is not None:
        logger.map_logger.info("Generate link details...")
    network = generate_link_details(network)

    if logger_file is not None:
        logger.map_logger.info("Generate movement details...")
    network = generate_movement_details(network)

    if logger_file is not None:
        logger.map_logger.info("Generate network connectors...")
    generate_network_connectors(network)

    if logger_file is not None:
        logger.map_logger.info("Map data processing done. (ACCURATE MODE)")

    # release the handler and close the file
    if logger_file is not None:
        for handler in logger.map_logger.handlers[:]:
            handler.close()
            logger.map_logger.removeHandler(handler)
    return network


def _load_intersection_name(network, name_file):
    """
    Add the name of intersection to the network

    :param network: `mtldp.mtlmap.Network`
    :param name_file: str name of the file
    :return: `mtldp.mtlmap.Network`
    """
    if name_file is None:
        return network
    with open(name_file, "r") as temp_file:
        all_lines = temp_file.readlines()

    for single_line in all_lines[1:]:
        node_id, name = single_line[:-1].split(",")
        if node_id in network.nodes.keys():
            network.nodes[node_id].name = name.split(":")[-1]
    return network

