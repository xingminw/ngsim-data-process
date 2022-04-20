from utils.ngsim_adapter import NgsimTrajectoryAdapter
from mtldp.processes import Region, build_region_network, \
    split_points_df_into_region, region_map_match, region_trajectory_calculation


file_location = 'E:/Data/Peachtree-Street-Atlanta-GA/NGSIM_Peachtree_Vehicle_Trajectories.csv'

# step 0: construct the region configuration.json file
config_region = Region('peachtree/configuration.json')

# step 1: build the region network
network = build_region_network(config_region, save_to_local=False)

# step 2: read the raw data
points_df = NgsimTrajectoryAdapter().load([file_location])[::10]

# step 3: split trajectory data into region and date
split_points_df_into_region(points_df, config_region, append=False)

# step 4: trajectory data map matching
region_map_match(config_region, ['1970-01-14'],
                 split_gap=False, load_map_buffer=True)

# step 5: trajectory calculation (add distance, performance measurements, etc.)
region_trajectory_calculation(config_region, '1970-01-14',
                              nodes_of_interest=None,
                              max_away_intersection=1e6,
                              max_away_road=1e6)
