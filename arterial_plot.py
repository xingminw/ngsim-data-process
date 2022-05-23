import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

traj_raw = pd.read_csv('peachtree/matched_trajs.csv')
link_length = pd.read_csv('peachtree/links.csv')

traj = pd.merge(traj_raw, link_length, on='link_id')
junctions = traj["junction_id"].unique()
junctions = junctions.astype(str)
links = traj["link_id"].unique()
nonarter_list = []
for link in links:
    od_points = link.split('_')
    if od_points[0] not in junctions or od_points[1] not in junctions:
        continue
    idx = traj[traj['link_id'] == link].index
    traj.loc[idx, 'arterial_id'] = 1

arterial_traj = traj.dropna(subset=['arterial_id'])
movements = arterial_traj['movement_id'].unique()
for movement in movements:
    points = movement.split('_')
    if points[0] not in junctions or points[1] not in junctions or points[2] not in junctions:
        continue
    idx = arterial_traj[arterial_traj['movement_id'] == movement].index
    arterial_traj.loc[idx, 'arterial_id'] = 0

arterial_traj = arterial_traj[arterial_traj['arterial_id'] == 1]
south_arterial = arterial_traj[arterial_traj['from_direction'] == 'N']
north_arterial = arterial_traj[arterial_traj['from_direction'] == 'S']

idx = south_arterial[south_arterial['link_id'] == ]

print()
