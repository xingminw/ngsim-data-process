"""
visualize the map data
"""

import json
import numpy as np
from ..utils import constants as utils


def overwrite_map_attributes(network, overwrite_json_file):
    """
    Overwrite the map attributes

    :param network:
    :param overwrite_json_file:
    """
    with open(overwrite_json_file, "r") as json_file:
        overwrite_dict = json.load(json_file)
    if "nodes" in overwrite_dict.keys():
        overwrite_node_dict = overwrite_dict["nodes"]
        for node_id, node_attrib in overwrite_node_dict.items():
            if not (node_id in network.nodes.keys()):
                continue
            for k, v in node_attrib.items():
                if k == 'name':
                    original_name = network.nodes[node_id].name
                    setattr(network.nodes[node_id], k, v + ':' + original_name)
                else:
                    setattr(network.nodes[node_id], k, v)

    if "segments" in overwrite_dict.keys():
        overwrite_segment_dict = overwrite_dict["segments"]
        for segment_id, segment_attrib in overwrite_segment_dict.items():
            if not (segment_id in network.segments.keys()):
                continue
            for k, v in segment_attrib.items():
                setattr(network.segments[segment_id], k, v)

    if "links" in overwrite_dict.keys():
        overwrite_link_dict = overwrite_dict["links"]
        for link_id, link_attrib in overwrite_link_dict.items():
            if not (link_id in network.links.keys()):
                continue
            for k, v in link_attrib.items():
                setattr(network.links[link_id], k, v)

    if "movements" in overwrite_dict.keys():
        overwrite_movement_dict = overwrite_dict["movements"]
        for movement_id, movement_attrib in overwrite_movement_dict.items():
            movement = network.movements[movement_id]
            if not (movement_id in network.movements.keys()):
                continue
            for k, v in movement_attrib.items():
                setattr(movement, k, v)
                if k == 'index':        # update the direction if movement index change
                    movement.update_dir()
    return network


def output_static_geometry_json(network, output_file=None,
                                lat_ahead=True):
    """
    Input the network, output the json file to display. The output ``.json`` is used to display the network
    in the web-based visualization tool: `[map web] <https://xingminw.github.io/mtldp/map.html>`_.

    :param network: `mtldp.mtlmap.Network`
    :param output_file: if ``None``, this will return the dict, else save to the file
    :param lat_ahead: latitude ahead or longitude ahead
    :return: ``None`` if the ``output_file`` is not empty, otherwise this function will return the ``dict``.
    """
    output_dict = {"segments": {}, "nodes": {}, "links": {}, "lanesets": {}}
    for link_id, link in network.links.items():
        geometry_list = get_geometry_list(link.geometry, lat_ahead)
        link_tag = "<p> link id: " + link.link_id + "<br/>"
        link_tag += f"from direction: {link.from_direction} <br/>"
        link_tag += "</p>"
        output_dict["links"][link_id] = {"geometry": geometry_list, "type": "arrow", "tag": link_tag}

    for laneset_id, laneset in network.lanesets.items():
        geometry_list = get_geometry_list(laneset.geometry, lat_ahead)
        laneset_tag = "<p> laneset id: " + laneset_id + "<br/>"
        laneset_tag += "speed limit: " + str(int(laneset.speed_limit / utils.MPH_TO_METERS_PER_SEC)) + " mph <br/>"
        laneset_tag += "lane number: " + str(int(laneset.lane_number)) + "<br/>"
        laneset_tag += f"direction: {laneset.turn_direction} <br/>"
        laneset_tag += "</p>"
        output_dict["lanesets"][laneset_id] = {"geometry": geometry_list, "type": "arrow", "tag": laneset_tag}

    for segment_id, segment in network.segments.items():
        geometry_list = get_geometry_list(segment.geometry, lat_ahead)
        segment_tag = "<p> segment id: " + segment_id + " <br/> "
        segment_tag += "lane number: " + str(int(segment.lane_number)) + "<br/>"
        segment_tag += "speed limit: " + str(int(segment.speed_limit / utils.MPH_TO_METERS_PER_SEC)) + "mph <br/>"
        segment_tag += "upstream node: " + segment.upstream_node.node_id + " <br/> "
        segment_tag += "downstream node: " + segment.downstream_node.node_id + " <br/> "
        downstream_directions = "".join(segment.downstream_directions_info.keys())
        segment_tag += f"from direction {segment.from_direction}-{downstream_directions}"
        segment_tag += "</p>"
        output_dict["segments"][segment_id] = {"geometry": geometry_list, "type": "arrow", "tag": segment_tag}

    for node_id, node in network.nodes.items():
        node_tag = "<p> node id: " + node.node_id + "<br/>"
        node_tag += "type: " + str(node.type.name) + "<br/>"
        # node_tag += "v/c ratio: " + str(np.round(node.v_c_ratio, 3))

        phase_details = {}
        movement_details = {}
        # add button for phase and movement
        if node.is_intersection():
            movement_list = node.movement_list
            node_tag += "<br / > Movement: "
            for movement in movement_list:
                if not (movement.movement_id in movement_details.keys()):
                    movement_details[movement.movement_id] = {"geometry": []}
                movement_geometry = movement.geometry
                geometry_list = get_geometry_list(movement_geometry, lat_ahead)
                node_tag += f"{movement.movement_id}: " \
                            f"<button onclick= \"clickMovementButton(\'{movement.movement_id}\', " \
                            f"\'{node_id}\')\">{movement.index}</button>  <br/>"
                movement_details[movement.movement_id]["geometry"].append(geometry_list)

        node_tag += "</p>"
        if lat_ahead:
            node_geometry = [node.latitude, node.longitude]
        else:
            node_geometry = [node.longitude, node.latitude]
        output_dict["nodes"][node_id] = \
            {"geometry": node_geometry,
             "tag": node_tag, "type": str(node.type.name),
             "color": get_color(0, 0.3),
             "phases": phase_details,
             "movements": movement_details}

    if lat_ahead:
        output_dict["bounds"] = [[network.bounds.min_lat, network.bounds.min_lon],
                                 [network.bounds.max_lat, network.bounds.max_lon]]
    else:
        output_dict["bounds"] = [[network.bounds.min_lon, network.bounds.min_lat],
                                 [network.bounds.max_lon, network.bounds.max_lat]]

    if output_file is None:
        return output_dict
    else:
        output_text = json.dumps(output_dict, indent=2)
        with open(output_file, "w") as temp_file:
            temp_file.write(output_text)
        return None


def get_geometry_list(geometry, lat_ahead=True):
    """
    Get a list of geometry coordination points of a Geometry object

    :param geometry: `mtldp.utils.Geometry`
    :param lat_ahead: bool, True if the user wants the geometry points to be [latitude, longitude], default True
    :return: list of geometry points [[lat1, lon1], [lat2, lon2]...]
    """
    lat_list = geometry.lat
    lon_list = geometry.lon
    geometry_list = []
    for idx in range(len(lat_list)):
        if not lat_ahead:
            geometry_list.append([lon_list[idx], lat_list[idx]])
        else:
            geometry_list.append([lat_list[idx], lon_list[idx]])
    return geometry_list


def get_color(val, marker=0.5):
    """
    Get color value corresponding to the input val

    :param val: float
    :param marker:
    :return:
    """
    hex_color_converter = '#%02x%02x%02x'
    color_1 = np.array([0, 255, 0])
    color_2 = np.array([255, 255, 0])
    color_3 = np.array([255, 0, 0])
    if val < 0:
        val = 0
    if val > 1:
        val = 1
    if val <= marker:
        color = val / marker * (color_2 - color_1) + color_1
    else:
        color = (val - marker) / (1 - marker) * (color_3 - color_2) + color_2
    return hex_color_converter % tuple([int(v) for v in color])


def _get_properties(item, attr_list) -> dict:
    """
    Get attributes of an item based on the input attribute name list

    :param item: an object
    :param attr_list: list of str
    :return: dict, key: name of the attribute, value: attribute
    """
    new_dict = {}
    object_dict = item.__dict__
    for attr in attr_list:
        if attr in object_dict.keys():
            new_dict[attr] = object_dict[attr]
    return new_dict


def line_to_geojson(item_list: list, attr_list: list) -> dict:
    """
    Get geojson dictionary of a list of line-like objects (ie. way, movement, link)
    Note that the object must have `mtldp.utils.Geometry` attribute

    :param item_list: list of objects
    :param attr_list: list of name of the attributes
    :return: dict in geojson format, "type": "FeatureCollection", "features": list
    """
    output = {"type": "FeatureCollection"}
    features = []
    for item in item_list:
        one_item = {"type": "Feature",
                    "geometry": {"type": "LineString", "coordinates": item.geometry.geometry2list()},
                    "properties": _get_properties(item, attr_list)
                    }
        features.append(one_item)
    output["features"] = features
    return output


def point_to_geojson(item_list: list, attr_list: list) -> dict:
    """
    Get geojson dictionary of a list of point-like objects (ie. node)
    Note that the object must have longitude and latitude attribute

    :param item_list: list of objects
    :param attr_list: list of name of the attributes
    :return: dict in geojson format, "type": "FeatureCollection", "features": list
    """
    output = {"type": "FeatureCollection"}
    features = []
    for point in item_list:
        one_item = {"type": "Feature",
                    "geometry": {"type": "Point", "coordinates": [point.longitude, point.latitude]},
                    "properties": _get_properties(point, attr_list)
                    }
        features.append(one_item)
    output["features"] = features
    return output


def network_to_geojson(network, node_attr="node_id", way_attr="way_id", segment_attr="segment_id",
                       laneset_attr="laneset_id", link_attr="link_id", movement_attr="movement_id", output_file=None):
    """
    Save network attributes to geojson
    Note that if an attribute is None, then the attribute will not be saved to geojson

    :param network: `mtldp.mtlmap.Network`
    :param node_attr: str or list of node attribute to be saved in geojson, default "node_id"
    :param way_attr: str or list of way attribute to be saved in geojson, default "way_id"
    :param segment_attr: str or list of segment attribute to be saved in geojson, default "segment_id"
    :param laneset_attr: str or list of laneset attribute to be saved in geojson, default "laneset_id"
    :param link_attr: str or list of link attribute to be saved in geojson, default "link_id"
    :param movement_attr: str or list of movement attribute to be saved in geojson, default "movement_id"
    :param output_file: if ``None``, this will return the dict, else save to the file
    :return: dict in geojson format, "type": "FeatureCollection", "bbox": bounds of network, "features": list
    """
    feature_list = []
    if node_attr is not None:
        node_attr = [node_attr] if type(node_attr) is str else node_attr
        feature_list += point_to_geojson(list(network.nodes.values()), node_attr)["features"]
    if link_attr is not None:
        link_attr = [link_attr] if type(link_attr) is str else link_attr
        feature_list += line_to_geojson(list(network.links.values()), link_attr)["features"]
    if way_attr is not None:
        way_attr = [way_attr] if type(way_attr) is str else way_attr
        feature_list += line_to_geojson(list(network.ways.values()), way_attr)["features"]
    if segment_attr is not None:
        segment_attr = [segment_attr] if type(segment_attr) is str else segment_attr
        feature_list += line_to_geojson(list(network.segments.values()), segment_attr)["features"]
    if laneset_attr is not None:
        laneset_attr = [laneset_attr] if type(laneset_attr) is str else laneset_attr
        feature_list += line_to_geojson(list(network.lanesets.values()), laneset_attr)["features"]
    if movement_attr is not None:
        movement_attr = [movement_attr] if type(movement_attr) is str else movement_attr
        feature_list += line_to_geojson(list(network.movements.values()), movement_attr)["features"]

    output_dict = {"type": "FeatureCollection", "bbox": network.bounds.boundingBox2list(), "features": feature_list}
    if output_file is None:
        return output_dict
    else:
        output_text = json.dumps(output_dict, indent=2)
        with open(output_file, "w") as temp_file:
            temp_file.write(output_text)
        return None
