import pandas as pd


def demand_and_turning_calibration(file):
    traj_data = pd.read_csv(file)
    junctions = traj_data["junction_id"].unique()
    flag = 0
    turning = []
    for junction in junctions:
        time = []
        distance = []
        junction_data = traj_data[traj_data["junction_id"] == junction]

        movements = junction_data["movement_id"].unique()
        for movement in movements:
            movement_data = junction_data[junction_data["movement_id"] == movement]
            trajs = movement_data["traj_id"].unique()
            links = movement.split('_')
            turning.append([movement, len(trajs), int(links[0]), links[1], links[2]])

    raw_turning = pd.DataFrame(turning, columns=['movement_id', 'volume', 'upstream', 'junction', 'downstream'])
    volume_sum = raw_turning.groupby(['junction', 'upstream']).sum().reset_index()

    volume_sum = volume_sum.rename(columns={'volume': 'volume_sum'})
    turning = pd.merge(raw_turning, volume_sum, on=['upstream','junction'])
    turning["turning_ratio"] = turning["volume"] / turning["volume_sum"]
    turning.to_csv("./output/turning.csv", index=None)

    turning_idx = turning.set_index("upstream")
    demand = turning_idx.drop(labels=junctions).reset_index()
    demand['volume_sum'] = demand['volume_sum'] * 4
    demand = demand[['upstream', 'volume_sum']]
    demand.drop_duplicates(inplace=True)
    demand = demand.rename(columns={'volume_sum': 'vph'})
    demand = demand.rename(columns={'upstream': 'downstream'})
    demand.to_csv('./output/demand.csv', index=None)



if __name__ == "__main__":
    demand_and_turning_calibration("peachtree/matched_trajs.csv")
