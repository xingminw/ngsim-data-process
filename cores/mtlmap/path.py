"""
to be done: path class
"""

from ..mtlmap.map_modes import GraphMode
from ..mtlmap.nodes_classes import NodeCategory
from ..utils.geometry import Geometry
from .utils import get_movement_list


class Path(object):
    """
    either init from OD pair or node list
    """
    def __init__(self, path_id=None):
        """

        :param path_id:
        """
        self.path_id = path_id
        self.origin_node = None
        self.destination_node = None
        self.network = None
        self.node_list = []
        self.link_list = []
        self.movement_list = []
        self.length = 0

        # set geometry
        self.geometry = None
        self.distance_by_movement = {}
        self.distance_by_link = {}
        self.distance_by_node = {}

    def init_from_node_list(self, network, node_id_list):
        if len(node_id_list) == 2:
            return self.init_from_od(network, node_id_list[0], node_id_list[1], init_all=True)
        elif len(node_id_list) > 2:
            path = Path()
            for idx in range(len(node_id_list) - 1):
                current_node = node_id_list[idx]
                next_node = node_id_list[idx + 1]
                local_path = Path().init_from_od(network, current_node, next_node, init_all=False)
                path = path + local_path
            path._general_init()
            return path
        else:
            raise NotImplementedError('Length of node id list no less than 2.')

    def init_from_od(self, network, start_node_id, end_node_id, init_all=True):
        self.network = network
        network.build_networkx_graph(GraphMode.LINK)
        path_dict = network.shortest_path_between_nodes(start_node_id, end_node_id)
        weight_val = path_dict['weight']
        node_id_list = path_dict['nodes']
        link_id_list = path_dict['edges']
        self.length = weight_val

        node_list = []
        link_list = []
        for nid in node_id_list:
            if nid in network.nodes.keys():
                node_list.append(network.nodes[nid])

        for lid in link_id_list:
            if lid in network.links.keys():
                link_list.append(network.links[lid])

        self.link_list = link_list
        self.node_list = node_list
        self.origin_node = self.node_list[0]
        self.destination_node = self.node_list[-1]
        self.movement_list = self._movement_list_from_link_list(link_list)

        if init_all:
            self._general_init()
        return self

    def isempty(self):
        if self.origin_node is None:
            return True

    def get_intersection_label(self, separate=None,
                               filter_signal=True):
        """
        Get the label and distance from

        :param separate: default None, e.g., if input ':', then fetch the contents before ':'
        :param filter_signal: if True, then only show signalized intersection
        :return:
        """
        distance_list = []
        label_list = []
        intersection_list = []
        for node_id, node_dis in self.distance_by_node.items():
            node = self.network.nodes[node_id]
            if separate is None:
                local_name = str(node.name)
            else:
                if node.name is None:
                    local_name = str(node.node_id)
                else:
                    if separate in node.name:
                        local_name = node.name.split(separate)[0]
                    else:
                        local_name = ''
            if filter_signal:
                if node.type != NodeCategory.SIGNALIZED:
                    continue
            distance_list.append(node_dis)
            label_list.append(local_name)
            intersection_list.append(node_id)
        return label_list, distance_list, intersection_list

    def _general_init(self):
        self._update_distance_dict()
        self.geometry = self._get_geometry()

    def _movement_list_from_link_list(self, link_list):
        """

        :param link_list:
        :return:
        """
        movement_list = []
        movement_id_list = get_movement_list(link_list)
        for mid in movement_id_list:
            if mid in self.network.movements.keys():
                movement_list.append(self.network.movements[mid])
        return movement_list

    def _update_distance_dict(self):
        self.distance_by_node[str(self.node_list[0])] = 0
        cumulative_distance = 0
        for idx in range(len(self.link_list)):
            link = self.link_list[idx]
            link_length = link.length
            cumulative_distance += link_length
            self.distance_by_link[str(link)] = cumulative_distance
            if idx < len(self.movement_list):
                self.distance_by_movement[str(self.movement_list[idx])] = cumulative_distance
            self.distance_by_node[str(self.node_list[idx + 1])] = cumulative_distance

    def _get_geometry(self):
        """
        Get the geometry of the OnewayArterial

        :return `mtldp.utils.Geometry`
        """
        lon, lat = [], []
        for link in self.link_list:
            lon.extend(link.geometry.lon)
            lat.extend(link.geometry.lat)
        geometry = Geometry(lon, lat)
        return geometry

    def __len__(self):
        return self.length

    def __add__(self, other):
        if self.isempty():
            if not other.isempty():
                return other

        if self.network != other.network:
            raise ValueError("Two paths should be in the same network")
        new_path = Path()
        if str(self.destination_node) == str(other.origin_node):
            new_path.origin_node = self.origin_node
            new_path.network = self.network
            new_path.destination_node = self.destination_node
            new_path.node_list = self.node_list[:-1] + other.node_list
            new_path.length = self.length + other.length
            new_path.link_list = self.link_list + other.link_list
            new_path.movement_list = self._movement_list_from_link_list(new_path.link_list)
            return new_path
        else:
            mid_path = Path().init_from_od(self.network, str(self.destination_node), str(other.origin_node))
            first_part = self + mid_path
            whole_path = first_part + other
            return whole_path


if __name__ == '__main__':
    import mtldp.mtlmap as mtlmap
    net = mtlmap.build_network_from_xml(region_name='birmingham',
                                        file_name='../../data/birmingham.osm', logger_file=None)
    print()
