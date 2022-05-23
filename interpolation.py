import pandas as pd
import mtldp.mtltrajs as mtltrajs
import mtldp.mtlmap as mtlmap
from tqdm import tqdm

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

# todo: call function get the traffic matrices, in application
# todo: interpolation: for every 1 second (only keep new points)
numeric_column = ["distance", "speed", "longitude", "latitude"]
for trip_id, traj in tqdm(trajs_dict.dict.items()):
    # if traj.traj_id == "1000-1163668":
    #     a = points_table.df.loc[points_table.df["traj_id"] == "1000-1163668"]
    #     print()
    new_traj = mtltrajs.interpolation(traj, numeric_column, resolution=0.2, degree=1, inplace=False)
    new_traj.df = new_traj.df.loc[new_traj.df["interpolated"] == 1]
    new_traj.df = new_traj.df.drop(columns="interpolated")
    trajs_dict.dict[trip_id] = new_traj

# interpolated_points_df = trajs_dict.get_points_df(attributes="all")
#
# interpolated_points_df.to_csv("peachtree/interpolated_trajs.csv", index=False)

# print()

# points_df = trajs_dict.get_points_df(attributes='all')
