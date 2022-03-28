import pandas as pd
from pyproj import Transformer
from draw_gps import draw_scatters
from ngsim_adapter import NgsimTrajectoryAdapter


file_location = 'C:/Data/Peachtree-Street-Atlanta-GA/NGSIM_Peachtree_Vehicle_Trajectories.csv'
# file_location = 'C:/Data/Lankershim-Boulevard-LosAngeles-CA/NGSIM__Lankershim_Vehicle_Trajectories.csv'

points_df = NgsimTrajectoryAdapter().load([file_location])
sampled_pts = points_df[::100]
lat_list = sampled_pts['latitude'].tolist()
lon_list = sampled_pts['longitude'].tolist()
speed_list = sampled_pts['speed'].tolist()
print()

draw_scatters(lat_list, lon_list, speed_list)

