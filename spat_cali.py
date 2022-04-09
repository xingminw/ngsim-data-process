import pandas as pd
import matplotlib.pyplot as plt

traj_data = pd.read_csv('peachtree/matched_trajs.csv')
junctions = traj_data["junction_id"].unique()
flag = 0
for junction in junctions:
    time = []
    distance = []
    junction_data = traj_data[traj_data["junction_id"] == junction]

    movements = junction_data["movement_id"].unique()
    if junction == junctions[0]:
        for movement in movements:
            movement_data = junction_data[junction_data["movement_id"] == movement]
            trajs = movement_data["traj_id"].unique()
            for traj in trajs:
                traj_data = movement_data[movement_data["traj_id"] == traj]
                time = traj_data["timestamp"].values
                distance = traj_data["distance"].values
                plt.plot(time, distance, color='gray')
            print(movement)
            plt.title(f"movement_id = {movement}")
            plt.show()
    else:
        continue
