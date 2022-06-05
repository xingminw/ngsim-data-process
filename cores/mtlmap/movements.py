import pandas as pd
from ..utils import logger, constants, geometry


class Movement(object):
    """
     A movement reflects the user perspective and is defined by the user type and the action that is taken (e.g.
     through, right turn, left turn)

     **Main Attributes**
        -``index``: phase id
        -``movement_id``: movement id
        -``upstream_link``: upstream link
        -``downstream_link``: downstream link
        -``node``: center node
        -``direction``: moving direction
        -``upstream_length``: upstream length
        -``protected``:
        -``geometry``:
        -``belonged_arterial``: belonged arterial object
    """

    def __init__(self):
        self.index = None
        self.movement_id = None
        self.upstream_link = None
        self.dedicated_turn_length = None
        self.downstream_link = None
        self.node = None

        self.direction = None       # "b", "r", "l", "s"
        self.upstream_length = None
        self.geometry = None
        self.laneset_list = []
        self.cum_lanset_length_list = []

        self.belonged_arterial = []

    def __str__(self):
        return self.movement_id

    def set_basic_info(self, upstream_link, downstream_link, node):
        self.upstream_link = upstream_link
        self.downstream_link = downstream_link
        self.node = node

    def update_dir(self):
        """
        update the turning string according to movement index

        :return:
        """
        if self.index <= 8:
            if self.index % 2 == 0:
                self.direction = 's'
            else:
                self.direction = 'l'
        elif 9 <= self.index <= 12:
            self.direction = 'r'
        else:
            self.direction = 'b'

    def get_geometry(self, from_laneset=False):
        """

        :param from_laneset:
        :return:
        """
        if not from_laneset:
            upstream_geometry = self.upstream_link.geometry
            downstream_geometry = self.downstream_link.geometry
            return geometry.Geometry(upstream_geometry.lon + downstream_geometry.lon,
                                     upstream_geometry.lat + downstream_geometry.lat)
        else:
            lat_list = []
            lon_list = []
            for laneset in self.laneset_list:
                laneset_geo = laneset.geometry
                lat_list += laneset_geo.lat
                lon_list += laneset_geo.lon
            downstream_geometry = self.downstream_link.geometry
            lat_list += downstream_geometry.lat
            lon_list += downstream_geometry.lon
            return geometry.Geometry(lon_list, lat_list)

    def to_dict(self, attr="all"):
        movement_dict = {}
        all_dict = self.__dict__
        if attr == "all":
            movement_dict = all_dict.copy()
            attr = all_dict.keys()
        else:
            for one_attr in attr:
                movement_dict[one_attr] = all_dict[one_attr]
        for link_info in {"upstream_link", "downstream_link", "node", "geometry"}.intersection(set(attr)):
            movement_dict[link_info] = str(all_dict[link_info])
        if "belonged_arterial" in attr:
            movement_dict["belonged_arterial"] = []
            for arterial in self.belonged_arterial:
                movement_dict["belonged_arterial"].append(str(arterial))

        return movement_dict

    def to_df(self, attr="all"):
        movement_dict = self.to_dict(attr=attr)
        return pd.DataFrame(movement_dict, index=[0])


def get_movement_from_dict(input_movement_dict):
    movement = Movement()
    movement.__dict__ = input_movement_dict.copy()
    movement.__dict__["geometry"] = geometry.get_geometry_from_str(input_movement_dict["geometry"])
    return movement


def generate_network_movements(network):
    """
    generate network movements

        Use node information in the network to generate network movements
    :param network:
    :return:
    """
    for node_id, node in network.nodes.items():
        if not node.is_intersection():
            continue
        for segment in node.upstream_segments:
            # print(segment.downstream_directions_info)
            for direction, downstream_segment in segment.downstream_directions_info.items():
                downstream_segment_id = downstream_segment.segment_id
                downstream_segment = network.segments[downstream_segment_id]
                upstream_link = segment.belonged_link
                downstream_link = downstream_segment.belonged_link

                movement = Movement()
                if upstream_link is None or downstream_link is None:
                    continue
                movement.set_basic_info(upstream_link, downstream_link, node)

                movement.index = constants.get_movement_id(segment.from_direction, direction)[0]

                upstream_link_id = upstream_link.link_id
                downstream_link_id = downstream_link.link_id
                movement_id = upstream_link_id + "_" + downstream_link_id.split("_")[-1]
                movement.movement_id = movement_id
                movement.direction = direction
                movement.geometry = movement.get_geometry()
                node.add_movement(movement)
                upstream_link.add_movement(movement)
                network.add_movement(movement)
    return network


def generate_movement_details(network):
    """
    Update the details of movement according to the laneset
    1) update the laneset_list

    :param network:
    :return:
    """
    for movement in network.movements.values():
        link = movement.upstream_link
        segment_list = link.segment_list
        movement_laneset_list = []
        for segment in segment_list:
            laneset_list = segment.laneset_list
            if len(laneset_list) == 1:
                movement_laneset_list.append(laneset_list[0])
            elif len(laneset_list) > 1:
                chosen_laneset = None
                for laneset in laneset_list:
                    if movement.direction in laneset.turn_direction:
                        chosen_laneset = laneset
                        break
                if chosen_laneset is None:
                    if logger.map_logger is not None:
                        logger.map_logger.warn(f'Laneset of {movement} cannot be found in segment {segment}')
                    chosen_laneset = laneset_list[0]
                movement_laneset_list.append(chosen_laneset)
            else:
                if logger.map_logger is not None:
                    logger.map_logger.error(f'No lanesets in segment {segment}')
        movement.laneset_list = movement_laneset_list
        movement.geometry = movement.get_geometry(from_laneset=True)
    return network


if __name__ == "__main__":
    pass
