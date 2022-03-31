import os
import json
import pandas as pd
import matplotlib.pyplot as plt
import mtldp.mtltrajs as mtltrajs
import mtldp.mtlmap as mtlmap

network = mtlmap.build_network_from_xml(region_name='peachtree',
                                        file_name='peachtree/peachtree_filtered.osm',
                                        mode=mtlmap.MapMode.ACCURATE)

# adding arterial
arterial_info_dict = {"S": ['2390850312', '69488055'],
                      "N": ['69488055', '2390850312']}
corridor = mtlmap.Arterial(network, 'peachtree',
                           input_dict=arterial_info_dict, putin_network=True,
                           ref_node='69421277')


points_df = pd.read_csv('peachtree/matched_trajs.csv')
points_table = mtltrajs.OverallPoints()
points_table.load_data(points_df)
trajs_dict = points_table.get_trajs_dict(groupby='traj_id',
                                         traj_attributes=['link_id', 'movement_id', 'junction_id'])

print()

# todo: call function get the traffic matrices
# todo: interpolation: for every 1 second (only keep new points)

points_df = trajs_dict.get_points_df(attributes='all')

time_list = [0, 1, 2, 3, 4]
# time_list = ['00:00', '00:02']
for i_time in time_list:
    link_id = "XXX"             # segment_id,...
    # todo: some functions to extract data from traffic images
    density_vector = img.get_density_vec(link_id, i_time)
    speed_vector = img.get_density_vec(link_id, i_time)
    cell_length_list = img.get_cell_length_list(link_id)
