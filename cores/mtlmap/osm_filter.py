"""
Extract the certain layer from the original osm xml file
"""

import io
import xml.etree.ElementTree as ET

from tqdm import tqdm
from time import sleep
from xml.dom import minidom


# pre-determined filter
filter_dict = {
    "highway": {"logic": "False", "tags": ["footway", "pedestrian", "steps", "service", "cycleway"]}
}


def osm_way_filter(file_name, customized_filter=None, output_file="filtered.osm"):
    """
    Filter the osm way according the customized_filter
        the nodes in the selected ways will be saved automatically
        other irrelevant elements will be removed

    :param file_name: input file name (.xml or .osm)
    :param customized_filter:
    :param output_file:
    :return:
    """
    if customized_filter is None:
        customized_filter = filter_dict
    original_map = ET.parse(file_name)
    map_root = original_map.getroot()

    new_map = ET.Element("osm")
    new_map.attrib = {"version": "0.6", "generator": "xingminw", "copyright": "Michigan Traffic Lab"}

    useful_nodes = []
    sleep(0.1)
    print("Filtering the way in osm...")
    sleep(0.1)
    for elem in tqdm(map_root):
        if elem.tag == "bounds":
            ET.SubElement(new_map, "bounds", elem.attrib)
        if elem.tag != "way":
            continue

        node_list = []
        way_attributes = {}
        for details in elem:
            if details.tag == "nd":
                node_list.append(details.attrib["ref"])
            if details.tag == "tag":
                way_attributes[details.attrib["k"]] = details.attrib["v"]

        selected_flag = False
        for key_word in customized_filter.keys():
            if not (key_word in way_attributes.keys()):
                continue
            kwd_value = way_attributes[key_word]
            filter_logic = customized_filter[key_word]["logic"] == "True"
            if filter_logic:
                if kwd_value in customized_filter[key_word]["tags"]:
                    selected_flag = True
            else:
                if not (kwd_value in customized_filter[key_word]["tags"]):
                    selected_flag = True

        if selected_flag:
            way_element = ET.SubElement(new_map, "way", elem.attrib)
            for node_id in node_list:
                ET.SubElement(way_element, "nd", {"ref": node_id})
                if not (node_id in useful_nodes):
                    useful_nodes.append(node_id)
            for kwd in way_attributes.keys():
                ET.SubElement(way_element, "tag", {"k": kwd, "v": way_attributes[kwd]})

    sleep(0.1)
    print("Filtering the node in osm...")
    sleep(0.1)
    for elem in tqdm(map_root):
        if elem.tag != "node":
            continue
        node_attrib = elem.attrib
        node_id = node_attrib["id"]
        if not (node_id in useful_nodes):
            continue
        node_elem = ET.SubElement(new_map, "node", node_attrib)
        for node_child in elem:
            ET.SubElement(node_elem, node_child.tag, node_child.attrib)

    output = ET.tostring(new_map)
    output_doc = minidom.parseString(output).toprettyxml()
    with io.open(output_file, "w", encoding="utf-8") as xml_file:
        xml_file.write(output_doc)
