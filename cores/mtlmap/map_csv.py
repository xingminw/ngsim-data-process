import os
import pandas as pd
from .nodes_classes import NodeCategory


def _list2string(obj, connector=" "):
    """
    Convert a list of object to str
    Note that the objects need to be able to convert to str

    :param obj: list objet to be saved to string
    :param connector: connector that connect two object, default " "
    :return: str
    """
    return connector.join(str(val) for val in obj)


def convert_junction_to_df(network):
    """
    Save the attributes of all nodes in a network to `pandas.DataFrame`

    :param network: `mtldp.mtlmap.Network`
    :return: `pandas.DataFrame`
    """
    column_name = ['city_id', 'region_id', 'junction_id', 'junction_name', 'movement_list', 'longitude', 'latitude',
                   'pedestrian', 'traffic_light', 'roundabout', 'ramp_type', 'pedestrian_island', 'degree',
                   'sup_arterial_id']
    df = pd.DataFrame(columns=column_name)
    for node in network.nodes.values():
        if node.is_intersection():
            junction = {'junction_id': node.node_id, 'junction_name': node.name, 'longitude': node.longitude,
                        'latitude': node.latitude, 'traffic_light': node.type == NodeCategory.SIGNALIZED}
            if node.upstream_links is not None:
                junction["degree"] = len(node.upstream_segments)
            if node.movement_list is not None and len(node.movement_list) >= 1:
                junction["movement_list"] = _list2string(node.movement_list)
            if len(node.belonged_sup_arterial) != 0:
                junction["sup_arterial_id"] = _list2string(node.belonged_sup_arterial, ";")
            df = df.append(junction, ignore_index=True)
    df["city_id"] = network.city_id
    df["region_id"] = network.region_name
    return df


def convert_segment_to_df(network):
    """
    Save the attributes of all segments in a network to `pandas.DataFrame`

    :param network: `mtldp.mtlmap.Network`
    :return: `pandas.DataFrame`
    """
    column_name = ['city_id', 'region_id', 'segment_id', 'segment_name', 'geometry', 'upstream_junction_id',
                   'downstream_junction_id', 'pair_segment_id', 'length', 'segment_type', 'link_id',
                   'direction', 'heading', 'lane_num', 'speed_limit', 'laneset_list']
    df = pd.DataFrame(columns=column_name)
    for seg in network.segments.values():
        segment = {'segment_id': seg.segment_id, 'direction': seg.from_direction,
                   'upstream_junction_id': seg.upstream_node.node_id,
                   'downstream_junction_id': seg.downstream_node.node_id, 'link_id': str(seg.belonged_link),
                   'geometry': str(seg.geometry), 'length': seg.length, 'heading': seg.heading,
                   'lane_num': seg.lane_number, 'speed_limit': seg.speed_limit}
        pair_id = list(seg.segment_id)
        pair_id[-1] = '1' if seg.segment_id[-1] == '0' else '0'
        pair_id = "".join(pair_id)
        if seg.laneset_list is not None and len(seg.laneset_list) >= 1:
            segment["laneset_list"] = _list2string(seg.laneset_list)
        if seg.segment_id[-1] == '1':
            # segment['main_segment_id'] = pair_id if pair_id in network.segments.keys() else None
            segment['pair_segment_id'] = seg.segment_id
        else:
            segment['pair_segment_id'] = pair_id if pair_id in network.segments.keys() else None
            # segment['main_segment_id'] = seg.segment_id
        df = df.append(segment, ignore_index=True)
    df["city_id"] = network.city_id
    df["region_id"] = network.region_name
    return df


def convert_connection_to_df(network):
    """
    Save the attributes of all connections in a network to `pandas.DataFrame`

    :param network: `mtldp.mtlmap.Network`
    :return: `pandas.DataFrame`
    """
    column_name = ['city_id', 'region_id', 'connection_id', 'connection_type',
                   'upstream_laneset', 'downstream_laneset', 'diverge_prop',
                   'priority']
    df = pd.DataFrame(columns=column_name)

    for cn in network.connectors.values():

        connection = {'connection_id': cn.connector_id, 'connection_type': cn.type}
        if cn.upstream_laneset is not None:
            connection['upstream_laneset'] = cn.upstream_laneset.laneset_id
        if cn.downstream_laneset is not None:
            connection['downstream_laneset'] = cn.downstream_laneset.laneset_id
        if cn.movement_id is not None:
            connection['movement_id'] = cn.movement_id
        if cn.diverge_proportion is not None:
            connection['diverge_prop'] = cn.diverge_proportion
        if cn.priority is not None:
            connection['priority'] = cn.priority
        df = df.append(connection, ignore_index=True)
    df["city_id"] = network.city_id
    df["region_id"] = network.region_name
    return df

def convert_movement_to_df(network):
    """
    Save the attributes of all movements in a network to `pandas.DataFrame`

    :param network: `mtldp.mtlmap.Network`
    :return: `pandas.DataFrame`
    """
    column_name = ['city_id', 'region_id', 'junction_id', 'movement_id',
                   'phase_id', 'upstream_link_id',
                   'downstream_link_id', 'type', 'geometry', 'arterial_id']
    df = pd.DataFrame(columns=column_name)

    for mv in network.movements.values():
        movement = {'junction_id': mv.node.node_id, 'phase_id': mv.index, 'movement_id': mv.movement_id,
                    'geometry': str(mv.geometry)}
        if mv.upstream_link is not None:
            movement['upstream_link_id'] = mv.upstream_link.link_id
        if mv.downstream_link is not None:
            movement['downstream_link_id'] = mv.downstream_link.link_id
        if len(mv.belonged_arterial) != 0:
            movement["arterial_id"] = _list2string(mv.belonged_arterial, ";")
        df = df.append(movement, ignore_index=True)
    df["city_id"] = network.city_id
    df["region_id"] = network.region_name
    return df


def convert_link_to_df(network):
    """
    Save the attributes of all links in a network to `pandas.DataFrame`

    :param network: `mtldp.mtlmap.Network`
    :return: `pandas.DataFrame`
    """
    column_name = ['city_id', 'region_id', 'link_id', 'link_name',
                   'upstream_junction_id', 'downstream_junction_id',
                   'length', 'from_direction', 'geometry', 'segment_list', 'arterial_id']
    df = pd.DataFrame(columns=column_name)
    for lk in network.links.values():
        link = {'link_id': lk.link_id, 'upstream_junction_id': lk.upstream_node.node_id,
                'downstream_junction_id': lk.downstream_node.node_id, 'length': lk.length,
                'from_direction': lk.from_direction,
                'segment_list': " ".join([val.segment_id for val in lk.segment_list])}

        if lk.geometry is not None and len(lk.geometry) != 0:
            link['geometry'] = str(lk.geometry)
        else:
            link['geometry'] = None
        if len(lk.belonged_arterial) != 0:
            link["arterial_id"] = _list2string(lk.belonged_arterial, ";")
        df = df.append(link, ignore_index=True)
    df["city_id"] = network.city_id
    df["region_id"] = network.region_name
    return df


def convert_corridor_to_df(network):
    """
    Save the attributes of all arterials in a network to `pandas.DataFrame`

    :param network: `mtldp.mtlmap.Network`
    :return: `pandas.DataFrame`
    """
    column_name = ['city_id', 'region_id', 'arterial_id', 'sup_arterial', 'geometry',
                   'junction_list', 'link_list', 'movement_list', 'length',
                   'from_direction', 'to_direction']
    df = pd.DataFrame(columns=column_name)
    for arterial in network.arterials.values():
        for oneway in arterial.oneways.values():
            oneway_row = {'geometry': str(oneway.geometry), 'length': oneway.length,
                          'from_direction': None, 'to_direction': oneway.direction,
                          'junction_list': _list2string(oneway.node_list), 'link_list': _list2string(oneway.link_list),
                          'movement_list': _list2string(oneway.movement_list), 'arterial_id': oneway.name,
                          'sup_arterial': arterial.arterial_id}
            df = df.append(oneway_row, ignore_index=True)
    df["city_id"] = network.city_id
    df["region_id"] = network.region_name
    return df


def convert_laneset_to_df(network):
    column_name = ["city_id", "region_id", "laneset_id",
                   "length", "speed_limit", "geometry", "lane_number",
                   "belonged_segment",
                   "belonged_link", "turning_direction"]
    df = pd.DataFrame(columns=column_name)
    for laneset in network.lanesets.values():
        laneset_info = {"laneset_id": laneset.laneset_id,
                        "belonged_segment": str(laneset.belonged_segment),
                        "belonged_link": str(laneset.belonged_link),
                        "turning_direction": laneset.turn_direction,
                        "length": laneset.length, "speed_limit": laneset.speed_limit,
                        "geometry": str(laneset.geometry),
                        "lane_number": laneset.lane_number}
        df = df.append(laneset_info, ignore_index=True)
    df["city_id"] = network.city_id
    df["region_id"] = network.region_name
    return df


def _get_arterial_direction(arterial, reverse=False):
    if not reverse:
        direction = f"{arterial.from_direction}2"
        # in case of one-way arterial
        if arterial.reverse_from_direction is not None:
            direction = direction + arterial.reverse_from_direction
        else:
            link_list = arterial.oneways[arterial.from_direction].link_list
            direction = direction + link_list[-1].from_direction
    else:
        direction = f"{arterial.reverse_from_direction}2{arterial.from_direction}"
    return direction


def convert_movement_arterial_to_df(network):
    column_name = ["city_id", "region_id", "arterial_id", "junction_id", "movement_id", "direction"]
    df = pd.DataFrame(columns=column_name)
    for arterial in network.arterials.values():
        direction = _get_arterial_direction(arterial)
        arterial_id = arterial.arterial_id
        for movement in arterial.oneways[arterial.from_direction].movement_list:
            movement_info = {"arterial_id": arterial_id, "direction": direction,
                             "movement_id": movement.movement_id}
            junction_id = movement.movement_id.split("_")[1]
            if junction_id not in network.nodes.keys():
                junction_id = movement.node.node_id
            movement_info["junction_id"] = junction_id
            df = df.append(movement_info, ignore_index=True)
        # in case of one-way arterial
        if arterial.reverse_from_direction is not None:
            direction = _get_arterial_direction(arterial, reverse=True)
            for movement in arterial.oneways[arterial.reverse_from_direction].movement_list:
                movement_info = {"arterial_id": arterial_id, "direction": direction,
                                 "movement_id": movement.movement_id}
                junction_id = movement.movement_id.split("_")[1]
                if junction_id not in network.nodes.keys():
                    junction_id = movement.node.node_id
                movement_info["junction_id"] = junction_id
                df = df.append(movement_info, ignore_index=True)
    df["region_id"] = network.region_name
    df["city_id"] = network.city_id
    return df


def save_network_to_csv(network, folder):
    """

    :param network: `mtldp.mtlmap.Network`
    :param folder: str path of the folder
    :return: None
    """
    print("Saving lanesets...")
    df = convert_laneset_to_df(network)
    df.to_csv(os.path.join(folder, "lanesets.csv"), index=False)
    print("Saving junctions...")
    convert_junction_to_df(network).to_csv(os.path.join(folder, "junctions.csv"), index=False)
    print("Saving arterials...")
    convert_corridor_to_df(network).to_csv(os.path.join(folder, "arterials.csv"), index=False)
    print("Saving links...")
    convert_link_to_df(network).to_csv(os.path.join(folder, "links.csv"), index=False)
    print("Saving movements...")
    convert_movement_to_df(network).to_csv(os.path.join(folder, "movements.csv"), index=False)
    print("Saving segments...")
    convert_segment_to_df(network).to_csv(os.path.join(folder, "segments.csv"), index=False)
    print("Saving connections...")
    convert_connection_to_df(network).to_csv(os.path.join(folder, "connections.csv"), index=False)
    # print("Saving movement-arterial relations...")
    # convert_movement_arterial_to_df(network).to_csv(os.path.join(folder, "movement_arterial.csv"), index=False)
