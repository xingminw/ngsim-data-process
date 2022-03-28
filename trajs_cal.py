import os
import warnings
import pandas as pd
import mtldp.mtlmap as mtlmap
import mtldp.mtltrajs as mtltrajs
from pandas.core.common import SettingWithCopyWarning

warnings.simplefilter("ignore", category=SettingWithCopyWarning)
warnings.simplefilter('ignore', UserWarning)

timezone = 'America/Detroit'
points_attributes = ['veh_id', 'trip_id', 'traj_id', 'speed',
                     'Lane_ID', 'timestamp', 'longitude', 'latitude',
                     'segment_id', 'link_id', 'movement_id', 'distance']
# load the network data
network = mtlmap.build_network_from_xml(region_name='peachtree',
                                        file_name='peachtree/peachtree_filtered.osm',
                                        mode=mtlmap.MapMode.ACCURATE)

# load the map matched trajectory data
matched_file = 'output/trajs_files/matched.csv'
matched_points_df = pd.read_csv(matched_file, dtype={'veh_id': str,
                                                     'trip_id': str})

points_table = mtltrajs.OverallPoints()
points_table.load_data(matched_points_df)

movement_table_dict = points_table.split_by_attr('movement_id')
calculated_df_list = []
for movement_id, movement_table in movement_table_dict.items():
    if movement_id is None or movement_id not in network.movements.keys():
        continue
    movement = network.movements[movement_id]
    node = movement.node
    node_id = node.node_id
    link = movement.upstream_link
    if link is None or movement.upstream_length is None:
        continue
    movement_trajs_dict = movement_table.get_trajs_dict(groupby='trip_id')
    movement_trajs_dict.split_by_gap(time_threshold=60, distance_threshold=100, extra_id=1)
    for traj_id, trajectory in movement_trajs_dict.dict.items():
        mtltrajs.trajectory_processing(trajectory, link, node, movement, timezone)
    cal_points_df = movement_trajs_dict.get_points_df(points_attributes)
    cal_points_df['junction_id'] = node_id
    calculated_df_list.append(cal_points_df)

final_points_df = pd.concat(calculated_df_list)
final_points_df.to_csv('output/trajs_files/results.csv', index=False)

