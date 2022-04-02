import os
import mtldp.mtltrajs as mtltrajs
import mtldp.mtlmap as mtlmap

from utils.ngsim_adapter import NgsimTrajectoryAdapter


file_location = 'E:/Data/Peachtree-Street-Atlanta-GA/NGSIM_Peachtree_Vehicle_Trajectories.csv'
fmm_module = mtltrajs.FmmModule('output/map_files',
                                'output/map_files/shp')

points_df = NgsimTrajectoryAdapter().load([file_location])[::10]
points_table = mtltrajs.OverallPoints()
points_table.load_data(points_df)

# spilt trajectory by gap
points_table.split_by_gap(time_gap=20, distance_gap=100)

# output trajectory folder
trajs_output_folder = 'output/trajs_files'
if not os.path.exists(trajs_output_folder):
    os.mkdir(trajs_output_folder)

tmp_input_file = f'{trajs_output_folder}/tmp_input.csv'
tmp_output_file = f'{trajs_output_folder}/temp_mr.csv'
points_table.output_fmm_file(tmp_input_file, attr='trip_id', resort=True)

fmm_module.run(tmp_input_file, tmp_output_file)

points_table.load_fmm_results(tmp_output_file)

network = mtlmap.build_network_from_xml(region_name='peachtree',
                                        file_name='peachtree/peachtree_filtered.osm',
                                        mode=mtlmap.MapMode.ACCURATE)
points_table.add_complete_mapinfo(network)
print('Output data...')
points_table.df.to_csv(f'{trajs_output_folder}/matched.csv', index=False)

