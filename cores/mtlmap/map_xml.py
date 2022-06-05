"""
load and output osm xml map data
"""

import io
import xml.etree.ElementTree as ET

from xml.dom import minidom

from . import nodes_classes as nd
from . import static_net as net

from .osm_ways import OsmWay

from ..utils.geometry import get_bounding_box


def load_xml_map(region_name, file_name, city_id=''):
    """
    Load the network from the osm xml file
    parse the way and node in osm xml file

    :param region_name: str
    :param file_name: str
    :param city_id: str, default ''
    :return: `mtldp.mtlmap.Network`
    """
    network = net.Network(region_name, city_id=city_id)

    original_map = ET.parse(file_name)
    map_root = original_map.getroot()
    for elem in map_root:
        if elem.tag == "bounds":
            # Boundary latitude and longitude
            network.bounds = get_bounding_box(elem.attrib)

        elif elem.tag == "way":
            node_list = []
            way_attrib = elem.attrib
            way_tags = {}
            for details in elem:
                if details.tag == "nd":
                    node_list.append(details.attrib["ref"])
                if details.tag == "tag":
                    way_tags[details.attrib["k"]] = details.attrib["v"]
            way = OsmWay(way_attrib["id"], node_list, way_attrib, way_tags)
            network.add_way(way)

        elif elem.tag == "node":
            node_attrib = elem.attrib
            node_tags = {}
            for details in elem:
                if details.tag == "tag":
                    node_tags[details.attrib["k"]] = details.attrib["v"]
            node = nd.Node(node_attrib["id"], node_attrib, node_tags)
            network.add_node(node)
    return network


def save_network_to_xml(network, output_file, directed=True):
    """
    save network to osm xml file

    :param network: :py:class:`mimap.Network`
    :param output_file: location of the output xml file
    :param directed: if true, output the segment instead since all segments are directed osm ways
    """
    new_map = ET.Element("osm")
    new_map.attrib = {"version": "0.6", "generator": "xingminw", "copyright": "Michigan Traffic Lab"}

    # dump the osm bounds
    if network.bounds is not None:
        ET.SubElement(new_map, "bounds", network.bounds.get_bound_dict(value_type=str))

    # dump the osm nodes
    for node_id, node in network.nodes.items():
        new_node = ET.SubElement(new_map, "node", node.osm_attrib)
        for node_tag_k, node_tag_v in node.osm_tags.items():
            # print(tag, content)
            ET.SubElement(new_node, "tag", {"k": node_tag_k, "v": node_tag_v})

    if not directed:
        for way_id, way in network.ways.items():
            new_way = ET.SubElement(new_map, "way", way.osm_attrib)
            for way_tag_k, way_tag_v in way.osm_tags.items():
                ET.SubElement(new_way, "tag", {"k": way_tag_k, "v": way_tag_v})
                # print(type(way_tag_k), type(way_tag_v), way_tag_k, way_tag_v)
            for node in way.node_list:
                ET.SubElement(new_way, "nd", {"ref": node.node_id})
    else:
        for seg_id, segment in network.segments.items():
            new_way = ET.SubElement(new_map, "way", segment.osm_attrib)
            for way_tag_k, way_tag_v in segment.osm_tags.items():
                ET.SubElement(new_way, "tag", {"k": way_tag_k, "v": way_tag_v})

            for node in segment.node_list:
                ET.SubElement(new_way, "nd", {"ref": node.node_id})

    output = ET.tostring(new_map)
    output_doc = minidom.parseString(output).toprettyxml()
    with io.open(output_file, "w", encoding="utf-8") as xml_file:
        xml_file.write(output_doc)
