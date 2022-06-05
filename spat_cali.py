import pandas as pd
import matplotlib.pyplot as plt


def spat_cali(file_path):
    traj_data = pd.read_csv(file_path)
    junctions = traj_data["junction_id"].unique()
    for junction in junctions:
        junction_data = traj_data[traj_data["junction_id"] == junction]

        movements = junction_data["movement_id"].unique()
        if junction == junctions[2]:
            for movement in movements:
                movement_data = junction_data[junction_data["movement_id"] == movement]
                trajs = movement_data["traj_id"].unique()
                if len(trajs) < 50:
                    continue
                for traj in trajs:
                    traj_data = movement_data[movement_data["traj_id"] == traj]
                    time = traj_data["timestamp"].values
                    distance = traj_data["distance"].values
                    plt.plot(time, distance, color='gray')
                print(movement)
                print(junction)
                plt.title(f"movement_id = {movement}")
                plt.show()
        else:
            continue


def net_spat_cali(spat_file, connection_file):
    spat_raw = pd.read_csv(spat_file)
    connection = pd.read_csv(connection_file)
    spat = spat_raw.rename(columns={'movement_index': 'movement_id'})
    laneset_spat = pd.merge(spat, connection, on='movement_id', how='left')
    laneset_spat = laneset_spat[['upstream_laneset', 'start_time', 'end_time']]
    laneset_spat.to_csv('calibration/laneset_spat.csv')





if __name__ == "__main__":
    # spat_cali('peachtree/matched_trajs.csv')
    net_spat_cali('calibration/spat.csv', 'D:/osm-map-parser/output/peachtree/connections.csv')
