import pandas as pd


def connection_calibration(stat_connections, cali_data):
    """

    :param stat_connections:
    :param cali_data:
    :return:
    """
    turning_ratio = pd.read_csv(cali_data)
    connections = pd.read_csv(stat_connections)
    net_turning = pd.merge(connections, turning_ratio, on='movement_id', how='left')
    movement_list = net_turning['movement_id'].values
    upstream_list = net_turning['upstream_laneset'].values

    connector_downstream = []
    for movement in movement_list:
        if movement in upstream_list:
            connector_downstream.append(movement)

    for downstream in connector_downstream:
        data_sum = net_turning[net_turning['upstream_laneset'] == downstream].sum()
        volume_sum = data_sum['volume']
        idx = net_turning[net_turning['movement_id'] == downstream].index
        net_turning.loc[idx, 'volume'] = volume_sum

    net_turning.dropna(subset=['volume'], inplace=True)

    # Adjust turning ratio
    net_volume = net_turning[['upstream_laneset', 'volume']]
    net_sum = net_volume.groupby(['upstream_laneset']).sum().reset_index()
    net_sum = net_sum.rename(columns={'volume': 'all_volume'})
    laneset_connection_raw = pd.merge(net_turning, net_sum, on='upstream_laneset')
    laneset_connection_raw['diverge_prop'] = laneset_connection_raw['volume'] / laneset_connection_raw['all_volume']
    laneset_connection = laneset_connection_raw[['connection_id', 'connection_type',
                                                 'upstream_laneset', 'downstream_laneset',
                                                 'diverge_prop']]
    laneset_connection = laneset_connection.rename(columns={'upstream_laneset': 'upstream_link',
                                                            'downstream_laneset': 'downstream_link'}
                                                   )
    laneset_connection['priority'] = 0

    # corrections
    idx = laneset_connection[laneset_connection['diverge_prop'] == 1].index
    laneset_connection.loc[idx, 'connection_type'] = 'ordinary'
    laneset_connection.to_csv('calibration/laneset_connection.csv', index=None)


def demand_calibration(stat_lanesets, demand_data):
    """

    :param stat_lanesets:
    :param demand_data:
    :return: pandas.DataFrame contains downstream laneset_id
    """
    upstream_node_list = []
    laneset_info = pd.read_csv(stat_lanesets)
    link_list = laneset_info["belonged_link"].values
    for link in link_list:
        od_node = link.split('_')
        upstream_node_list.append(od_node[0])
    laneset_info["upstream"] = upstream_node_list
    laneset_info = laneset_info.rename(columns={"upstream": "downstream"})
    demand = pd.read_csv(demand_data)
    demand["downstream"] = demand["downstream"].astype(str)
    laneset_demand_raw = pd.merge(demand, laneset_info, on="downstream")
    dup_laneset = laneset_demand_raw.duplicated('downstream', keep=False)
    idx = dup_laneset[dup_laneset == True].index
    laneset_demand_raw.loc[idx, 'vph'] /= 2
    laneset_demand = laneset_demand_raw[['laneset_id', 'vph']]
    laneset_demand = laneset_demand.reset_index()
    laneset_demand.rename(columns={'index': 'demand_id', 'laneset_id': 'downstream'})
    laneset_demand.to_csv("calibration/laneset_demand.csv", index=None)


if __name__ == "__main__":
    demand_calibration('D:/osm-map-parser/output/peachtree/lanesets.csv', 'output/demand.csv')
    connection_calibration('D:/osm-map-parser/output/peachtree/connections.csv', 'output/turning.csv')
    print()
