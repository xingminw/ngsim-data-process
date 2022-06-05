"""
This file is to build the connectors of the network
"""
from ..utils import logger
from .nodes_classes import NodeCategory
from enum import Enum


class ConnectionType(Enum):
    ORDINARY = 1
    DIVERGE = 2
    MERGE = 3


class Connector(object):
    """
    Connector corresponds to a upstream laneset and downstream laneset(s)
    only diverge exists, do not record converge
    """

    def __init__(self):
        self.connector_id = None
        self.upstream_laneset = None
        self.downstream_laneset = None
        self.movement_id = None
        self.type = None

        # # priority class: 0 > 1 > 2 > ...
        self.priority = 0
        # todo: this is not added yet
        self.conflict_points = []

        self.diverge_proportion = 1
        self.belonged_node = None

        self.direction = ""
        self.upstream_origin = False
        self.downstream_destination = False

        self.controlled_node = None
        self.phase_id = None

    # def to_dict(self, attr="all"):
    #     all_dict = self.__dict__
    #     connector_dict = {}
    #     if attr == "all":
    #         connector_dict = all_dict.copy()
    #         attr = all_dict.keys()
    #     for one_attr in attr:
    #         if type(all_dict[one_attr]) is list:
    #             connector_dict[one_attr] = [str(item) for item in all_dict[one_attr]]
    #         else:
    #             connector_dict[one_attr] = str(all_dict[one_attr])
    #
    #     return connector_dict

    def __str__(self):
        return self.connector_id


def generate_network_connectors(network):
    """
    Build all connectors

    :param network: `cores.mtlmap.Network`
    :return: `cores.mtlmap.Network`
    """
    for laneset_id, laneset in network.lanesets.items():
        downstream_list = laneset.downstream_laneset_list
        if not downstream_list:
            # The laneset is the end laneset
            continue

        if len(downstream_list) == 1:
            ordinary_connector = build_connector(laneset, downstream_list[0])
            ordinary_connector.type = 'ordinary'
            network.connectors.update({ordinary_connector.connector_id: ordinary_connector})
        else:
            for downstream_laneset in downstream_list:
                diverge_connector = build_connector(laneset, downstream_laneset)
                diverge_connector.type = 'diverge'
                network.connectors.update({diverge_connector.connector_id: diverge_connector})
    return network


def build_connector(upstream_laneset, downstream_laneset):
    connector = Connector()
    connector.connector_id = upstream_laneset.laneset_id + '_' + downstream_laneset.laneset_id
    connector.upstream_laneset = upstream_laneset
    connector.downstream_laneset = downstream_laneset
    upstream_link = upstream_laneset.belonged_link.link_id
    downstream_link = downstream_laneset.belonged_link.link_id
    if upstream_link == downstream_link:
        connector.movement_id = downstream_laneset.laneset_id
        return connector

    down_idx = downstream_link.split('_')
    connector.movement_id = upstream_link + '_' + down_idx[1]

    return connector
