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
