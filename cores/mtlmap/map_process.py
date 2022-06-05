from copy import deepcopy
from .osm_ways import OsmWay, update_way_geometry

from ..utils import logger


def split_traverse_intersection_way(network):
    """
    split the osm way that traversed intersection,
        the split segments will inherit all the tag of the father way

    :param network: `mtldp.mtlmap.Network`
    :return: `mtldp.mtlmap.Network`
    """
    cut_way_dict = {}
    for way_id, way in network.ways.items():
        node_list = way.node_list
        for idx, node in enumerate(node_list):
            # node_id = node_list[idx]
            # node = network.nodes[node_id]

            # continue if the node is not an intersection
            if not node.is_intersection():
                continue
            # continue if there is no way traversing the node
            if len(node.traverse_ways) == 0:
                continue
            # continue if this is not the way traversing the intersection
            if not (way_id in node.traverse_ways):
                continue

            # record the cut node indices
            if not (way_id in cut_way_dict.keys()):
                cut_way_dict[way_id] = []

            cut_way_dict[way_id].append(idx)

    for way_id in cut_way_dict.keys():
        way = network.ways[way_id]
        node_list = way.node_list
        cut_node_index = cut_way_dict[way_id]

        index_cursor = 0

        new_way_index_list = []
        new_way_nodes_list = []
        for new_way_idx in range(len(cut_node_index)):
            current_index = cut_node_index[new_way_idx]
            new_node_list = node_list[index_cursor: current_index + 1]
            index_cursor = current_index
            new_way_index_list.append(new_way_idx)
            new_way_nodes_list.append(new_node_list)

        new_way_index_list.append(len(cut_node_index))
        new_way_nodes_list.append(node_list[index_cursor:])

        for new_idx in range(len(new_way_index_list)):
            new_way_idx = new_way_index_list[new_idx]
            new_node_list = new_way_nodes_list[new_idx]
            if len(new_node_list) <= 1:
                if logger.map_logger is not None:
                    logger.map_logger.warning("node number less than 2 when splitting way at " + way_id)
                continue

            new_way_id = way_id + "" + str(new_way_idx)
            if new_way_id in network.ways.keys():
                if logger.map_logger is not None:
                    logger.map_logger.warning("way id" + new_way_id + "already exists! Try adding 123")

                new_way_id += "123"
                if new_way_id in network.ways.keys():
                    if logger.map_logger is not None:
                        logger.map_logger.error("way id" + new_way_id + "already exists!")
                    exit()
            # create new way
            new_map_attrib = deepcopy(way.osm_attrib)
            new_map_attrib["id"] = new_way_id
            new_map_attrib["user"] = "xingminw"
            new_map_attrib["action"] = "split-way"
            new_way = OsmWay(new_way_id, osm_attrib=new_map_attrib,
                             osm_tags=way.osm_tags, node_list=new_node_list)
            new_way.update_way_geometry()
            network.add_way(new_way)
            # update_way_geometry(network, new_way_id)

        # delete the original way
        del network.ways[way_id]
    return network

