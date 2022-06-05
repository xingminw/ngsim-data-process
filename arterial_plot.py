import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import cores.mtlmap as mtlmap


traj_data = pd.read_csv('peachtree/matched_trajs.csv')
network = mtlmap.build_network_from_xml(region_name='peachtree',
                                        file_name='peachtree/peachtree_filtered.osm',
                                        mode=mtlmap.MapMode.ACCURATE)
arterial_info_dict = {"S": ['2390850312', '69488055'],
                      "N": ['69488055', '2390850312']}

corridor = mtlmap.Arterial(network, 'peachtree',
                           input_dict=arterial_info_dict, putin_network=True,
                           ref_node='69421277')
arterial_laneset_dict = {}
for arterial_dir, arterial in corridor.oneways.items():
    distance_dict = arterial.distance_by_movement
    movement_list = distance_dict.keys()
    through_traj = traj_data[traj_data['movement_id'].isin(movement_list)]
    x_min = through_traj['timestamp'].min()
    x_max = through_traj['timestamp'].max()
    through_traj['timestamp'] = through_traj['timestamp'] - x_min
    for movement in movement_list:
        through_traj.loc[through_traj['movement_id'] == movement, 'distance'] += distance_dict[movement]
        plt.hlines(distance_dict[movement], 0, x_max - x_min, colors="r", linestyles="dashed")
    trajs = through_traj['traj_id'].unique()
    for traj in trajs:
        traj = through_traj[through_traj["traj_id"] == traj]
        time = traj["timestamp"].values
        distance = traj['distance'].values
        plt.plot(time, distance, color='gray', alpha=0.4)
    ax = plt.gca()
    if arterial_dir == 'S':
        ax.invert_yaxis()
    plt.xlabel('timestamp')
    plt.ylabel('distance')
    plt.title(f'{arterial_dir}-direction arterial')
    plt.show()

    connections = pd.read_csv('D:/osm-map-parser/output/peachtree/connections.csv')
    laneset_list = []
    print(movement_list)
    upstream_laneset = None
    downstream_laneset = None
    for movement in movement_list:
        connection = connections[connections['movement_id'] == movement]
        upstream_laneset = connection['upstream_laneset'].values.tolist()[0]
        if upstream_laneset != downstream_laneset:
            laneset_list.append(downstream_laneset)
        downstream_laneset = connection['downstream_laneset'].values.tolist()[0]
        laneset_list.append(upstream_laneset)

    laneset_list.append(downstream_laneset)

    arterial_laneset_dict.update({arterial_dir: laneset_list})
