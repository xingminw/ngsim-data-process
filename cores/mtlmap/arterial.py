from .path import Path


class Arterial(object):
    """
    Class for two corridors in two directions

    **Main Attributes**
        -``.arterial_id``: str, id of the arterial
        -``.oneways``: dict, key: from direction, value: `mtldp.mtlmap.OnewayArterial`
        -``.node_list``: list of `mtldp.mtlmap.Node` along from_direction
        -``.directions``: list of directions
        -``.from_direction``: str
        -``.reverse_from_direction``: str
        -``.from_direction_length``: float
        -``.reverse_from_direction_length``: float
        -``.geometry``: `mtldp.utils.Geometry`
    """

    def __init__(self, network, arterial_id: str, input_dict: dict,
                 putin_network: bool = True, ref_node=None):
        """
        initialize the arterial

        :param network:
        :param arterial_id:
        :param input_dict: {"E": [start_node, (mid_node), end_node], "W": [start_node, end_node]}
        :param putin_network: True to put the arterial in the network, default True
        """
        # set self.arterial_id from input
        self.arterial_id = arterial_id

        self.ref_node = ref_node
        self.oneways = {}
        self._generate_oneway(network, input_dict)
        if putin_network:
            network.add_arterial(self)

    def get_node_list(self, stype='signalized'):
        node_id_list = []
        node_list = []
        for oneway in self.oneways.values():
            oneway_node_list = oneway.node_list
            for node in oneway_node_list:
                if node.type == stype:
                    node_id = str(node)
                    if not (node_id in node_id_list):
                        node_id_list.append(node_id)
                        node_list.append(node)
        return node_list

    def _generate_oneway(self, network, input_dict) -> None:
        """

        :param network:
        :param input_dict:
        :return:
        """
        # build the network in Link level for finding the shortest path between two nodes
        for direction, node_list in input_dict.items():
            oneway = OnewayArterial(network, self, direction, node_list)
            self.oneways[direction] = oneway

    def __str__(self):
        return self.arterial_id

    def __len__(self):
        return len(self.oneways)


class OnewayArterial(Path):
    """
    Class for a corridor in a certain direction

    **Main Attributes**
        -``.sup_arterial``: `mtldp.mtlmap.Arterial`
        - ``.node_list``: list of `mtldp.mtlmap.Node`
        - ``.from_direction``: the direction that the OnewayArterial is from
        - ``.link_list``: list of `mtldp.mtlmap.Link` along from_direction
        - ``.movement_list``: list of `mtldp.mtlmap.Movement` along from_direction
        - ``.to_direction``: to_direction of the OnewayArterial
        - ``.geometry``: `mtldp.utils.Geometry`
        - ``.name``: str, ie. "Plymouth W to E", where W is the from_direction and E is the to_direction
    """

    def __init__(self, network, sup_arterial: Arterial, direction: str, node_list: list):
        """
        Initialize the OnewayArterial

        :param network: `mtldp.mtlmap.Network`
        :param sup_arterial:
        :param node_list: list of node_id, MUST be given along the direction of from_direction
        :param direction: optional, str, name of the OnewayArterial, ie. "plymouth"
        """
        # the super arterial that self belongs to
        super().__init__()
        self.sup_arterial = sup_arterial
        self.direction = direction
        self.name = self._set_name(sup_arterial.arterial_id)
        self.init_from_node_list(network, node_list)

    def _set_name(self, name) -> str:
        """
        Set name of the OnewayArterial

        :param name: str
        """
        if self.direction == "E":
            to_direction = "east"
        elif self.direction == "W":
            to_direction = "west"
        elif self.direction == "S":
            to_direction = "south"
        elif self.direction == "N":
            to_direction = "north"
        else:
            to_direction = "null"
        return f"{name} {to_direction}bound"

    def get_trip_ts(self, trip):
        time_ls, distance_ls = [], []
        return time_ls, distance_ls

    def filter_trip_dict(self, trip_dict):
        """

        :param trip_dict:
        :return:
        """
        pass

    def split_side_street(self, trip_dict):
        pass

    def __str__(self):
        return self.name


if __name__ == "__main__":
    pass
