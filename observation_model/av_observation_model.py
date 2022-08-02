from ctm_network_adapter.ctm_adapter import CTMAdapter
from tqdm import tqdm
from utils import get_polar_coordinates, \
    get_vehicle_angle_interval, size_of_interval, \
    get_automated_vehicle
import portion as itv
import obs_utils
import numpy as np


class AVObservation(object):

    def __init__(self, ground_truth_traj, av_list, ctm_network, mtl_network):

        self.ground_truth_traj = ground_truth_traj
        self.av_list = av_list
        self.ctm_network = ctm_network
        self.mtl_network = mtl_network
        self.adapter = None
        self.av_traj = None

        self.times = None

        self.automated_vehicle_by_time = None
        self.gd_points_by_time = None
        self.observation_dict = {}
        self.cur_events = {}

    def run(self):
        self._initialize()
        for i_t in tqdm(self.times):
            self._step(i_t)
            self.ctm_network.step(int(i_t))
            # self._update()
            print()

    def _update(self):
        if self.cur_events is None:
            return
        update_mean = self.ctm_network.veh_num_vec
        update_variance = self.ctm_network.veh_cov_matrix

        for obs_id, obs_details in self.cur_events.items():

            measurement_h = obs_details['h']
            measurement_m = obs_details['m']
            measurement_v = obs_details['v']

            # standard kalman filter algorithm
            residual = measurement_m - np.matmul(measurement_h, update_mean)
            residual_var = np.matmul(measurement_h, update_variance)
            residual_var = np.matmul(residual_var, measurement_h.T)
            residual_var += measurement_v
            kalman_gain = np.matmul(update_variance, measurement_h.T)
            kalman_gain = np.matmul(kalman_gain, np.linalg.inv(residual_var))

            update_mean = update_mean + np.matmul(kalman_gain, residual)
            update_var = np.matmul(kalman_gain, measurement_h)
            update_var = np.identity(update_var.shape[0]) - update_var
            update_var = np.matmul(update_var, update_variance)
            update_variance = update_var

        self.num_variance = update_variance
        self.density_variance = update_variance

    def _step(self, time):
        self._get_current_data(time)
        self._generate_observation(time)
        self._generate_observation_matrix(time)

    def _initialize(self):
        self.adapter = CTMAdapter(self.ctm_network, self.mtl_network)
        self.ground_truth_traj = self.adapter.generate_adapted_points(self.ground_truth_traj)
        self.ground_truth_traj['timestamp'] -= self.ground_truth_traj['timestamp'].min()
        self.av_traj = self.ground_truth_traj[self.ground_truth_traj['veh_id'].isin(av_list)]
        self.automated_vehicle_by_time = dict(tuple(self.av_traj.groupby('timestamp')))
        self.gd_points_by_time = dict(tuple(self.ground_truth_traj.groupby('timestamp')))
        self.times = sorted(self.ground_truth_traj['timestamp'].unique())

    def _get_current_data(self, time):
        self.av_points = self.automated_vehicle_by_time.get(time, None)
        self.gd_points = self.gd_points_by_time[time]
        if self.av_points is not None:
            self.cur_automated_vehicles = self.av_points['veh_id'].unique()

    def _generate_observation(self, time):
        if self.av_points is None:
            return

        observable_vehicles = []
        overall_observation_df = None
        obs_dfs = []
        for av_id in self.cur_automated_vehicles:
            obs_vehicles, obs_df = self._get_observed_vehicle(av_id, self.gd_points)
            observable_vehicles += obs_vehicles
            if not obs_df.empty:
                obs_dfs.append(obs_df)

        if len(observable_vehicles) > 0:
            overall_observation_df = pd.concat(obs_dfs)

        self.observation_dict[time] = overall_observation_df
        self.obs_points = overall_observation_df

    def _get_vehicle_within_range(self, veh_id, point_df,
                                  angle_min, angle_max, radius_range):
        """
        :param veh_id:
        :param point_df:
        :param angle_min:
        :param angle_max:
        :param radius_range:
        :return:
        """
        road_width = 3.5
        vehicle_width = 2
        vehicle_length = 5

        automated_vehicle_df = point_df.loc[point_df["trip_id"] == veh_id]
        automated_vehicle_lane_index = automated_vehicle_df["Lane_ID"].iloc[0]
        automated_vehicle_segment_id = automated_vehicle_df["segment_id"].iloc[0]
        automated_vehicle_lane_pos = automated_vehicle_df["distance"].iloc[0]
        automated_vehicle_movement_id = automated_vehicle_df["movement_id"].iloc[0]
        # vehicle from the same direction
        same_direction_df = point_df.loc[(point_df["trip_id"] != veh_id) &
                                         ((point_df["segment_id"] == automated_vehicle_segment_id) |
                                          (point_df["movement_id"] == automated_vehicle_movement_id)) &
                                         (point_df["distance"] <= automated_vehicle_lane_pos + radius_range) &
                                         (point_df["distance"] >= automated_vehicle_lane_pos - radius_range)]

        obs_df_columns = list(point_df.columns) + ["angle", "radius", "interval", "same_dir", "av_id"]
        ideal_observation_list = []
        for row in same_direction_df.itertuples(index=False):
            lane_index = row.Lane_ID
            index_diff = lane_index - automated_vehicle_lane_index
            lateral_diff = row.distance - automated_vehicle_lane_pos
            vertical_diff = index_diff * road_width
            angle, radius = get_polar_coordinates(lateral_diff, vertical_diff)
            vehicle_itv = get_vehicle_angle_interval(lateral_diff, vertical_diff,
                                                     vehicle_width, vehicle_length)

            if (angle <= angle_min) or (angle >= angle_max):
                continue
            if radius >= radius_range:
                continue

            current_row = list(row) + [angle, radius, vehicle_itv, True, veh_id]
            ideal_observation_list.append(current_row)

        # vehicle from the other direction
        mtl_network = self.mtl_network
        if automated_vehicle_segment_id in mtl_network.segments.keys():
            edge = mtl_network.segments[automated_vehicle_segment_id]
            opposite_segment = edge.opposite_segment
        else:
            edge = None
            opposite_segment = None
        if opposite_segment is not None:
            opposite_min_dis = edge.length - automated_vehicle_lane_pos - radius_range
            opposite_max_dis = edge.length - automated_vehicle_lane_pos + radius_range
            opposite_direction_df = point_df.loc[(point_df["trip_id"] != veh_id) &
                                                 (point_df["segment_id"] == opposite_segment.segment_id) &
                                                 (point_df["distance"] < opposite_max_dis) &
                                                 (point_df["distance"] >= opposite_min_dis)]

            for row in opposite_direction_df.itertuples(index=False):
                land_diff = len(edge.lane_list) + len(opposite_segment.lane_list) - 1 - \
                            automated_vehicle_lane_index - row.lane_id
                vertical_diff = land_diff * road_width
                lateral_diff = edge.length - row.lane_dis - automated_vehicle_lane_pos
                angle, radius = get_polar_coordinates(lateral_diff, vertical_diff)
                vehicle_itv = get_vehicle_angle_interval(lateral_diff, vertical_diff,
                                                         vehicle_width, vehicle_length)

                if (angle <= angle_min) or (angle >= angle_max):
                    continue
                if radius >= radius_range:
                    continue
                current_row = list(row) + [angle, radius, vehicle_itv, False, veh_id]
                ideal_observation_list.append(current_row)
        ideal_observation_df = pd.DataFrame(ideal_observation_list, columns=obs_df_columns)
        return ideal_observation_df

    @staticmethod
    def _get_clear_viewed_vehicle(ideal_observation_df,
                                  angle_min, angle_max, min_viewed_angle):
        """
        get the clear viewed vehicle given the observation list

        :param ideal_observation_df:
        :param angle_min:
        :param angle_max:
        :param min_viewed_angle:
        :return:
        """
        observable_range = itv.closed(angle_min, angle_max)
        ideal_observation_df = ideal_observation_df.sort_values(['radius'], ascending=[True])

        column_num = len(ideal_observation_df.index)
        observed_vehicles = []
        observable_flag_list = []
        for idx in range(column_num):
            current_row = ideal_observation_df.iloc[idx, :]
            vehicle_id, angle, radius, local_itv = \
                current_row.trip_id, current_row.angle, current_row.radius, current_row.interval
            viewed_interval = observable_range.intersection(local_itv)
            if size_of_interval(viewed_interval) >= min_viewed_angle:
                observed_vehicles.append(vehicle_id)
                observable_flag_list.append(True)
            else:
                # observed_vehicles.append(vehicle_id)
                observable_flag_list.append(False)
            observable_range = observable_range.difference(local_itv)

        ideal_observation_df["observed"] = observable_flag_list
        return observed_vehicles, ideal_observation_df

    def _get_observed_vehicle(self, veh_id, point_df, angle_min=-180,
                              angle_max=180, radius_range=100, min_angle=2):
        """
        Get the observed vehicle

        :param veh_id:
        :param point_df:
        :param angle_min:
        :param angle_max:
        :param radius_range:
        :param min_angle:
        :return:
        """
        ideal_observation_df = \
            self._get_vehicle_within_range(veh_id, point_df,
                                           angle_min, angle_max, radius_range)
        observed_vehicles, observation_df = \
            self._get_clear_viewed_vehicle(ideal_observation_df,
                                           angle_min, angle_max, min_angle)
        return observed_vehicles, observation_df

    def _generate_observation_matrix(self, time):
        if self.av_points is None:
            return
        obs_points = self.observation_dict[time]
        events = self._get_observation_events(self.av_points, obs_points)
        self.cur_events = events

    def _get_observation_events(self, cv_points, av_observations, av_mode=True):

        utilized_events = {}
        stop_threshold = 0.1
        free_flow_threshold = 12
        transition_speed_threshold = 5
        obs_location_dict = {}

        free_flow_points = cv_points[cv_points['speed'] >= free_flow_threshold]
        stop_points = cv_points[cv_points['speed'] <= stop_threshold]

        free_flow_events = self._get_free_flow_events(free_flow_points)
        # self._get_stop_events(stop_points)
        if av_mode:
            self._get_av_events(av_observations)
        utilized_events.update(free_flow_events)

        return utilized_events

    def _get_free_flow_events(self, points_df):
        if points_df.empty:
            return {}
        free_flow_events = obs_utils.get_free_flow_event(points_df, self.ctm_network)

        return free_flow_events

    def _get_av_events(self, points_df):
        if points_df is None:
            return {}
        av_events = obs_utils.get_observation_events(points_df, self.ctm_network)

        return av_events

    def get_stop_events(self, points_df):
        if points_df.empty:
            return {}
        stop_events = obs_utils.get_stop_event(points_df, self.ctm_network)

        return stop_events


if __name__ == "__main__":
    import pandas as pd
    import cores.mtlmap as mtlmap
    from ctm import load_ctm

    traj = pd.read_csv('../peachtree/interpolated_trajs.csv')

    mtl_net = mtlmap.build_network_from_xml(region_name='peachtree',
                                            file_name='../peachtree/peachtree_filtered.osm',
                                            mode=mtlmap.MapMode.ACCURATE)
    ctm_net = load_ctm.load_ctm_network("../data/peachtree", cell_length=20, time_interval=1, sub_steps=10)
    av_list = get_automated_vehicle(traj, 0.1)
    av_observation = AVObservation(traj, av_list, ctm_net, mtl_net)
    av_observation.run()
    observation_df = pd.DataFrame.from_dict(av_observation.observation_dict)
    print()
