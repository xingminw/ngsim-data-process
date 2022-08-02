import numpy as np
from obs_utils import get_free_flow_event, get_stop_event_model



def get_av_observation_model(ctm_link, observation_dict, red_light,
                             cv_mode=False, stop_events=True, free_flow_events=True,
                             av_observations=True):
    """


    :param ctm_link:
    :param observation_dict:
    :param red_light:
    :param cv_mode:
    :param stop_events:
    :param free_flow_events:
    :param av_observations:
    :return:
    """
    stop_threshold = 0.1
    free_flow_threshold = 12
    transition_speed_threshold = 5
    obs_location_dict = {}
    stop_locations = []
    free_flow_locations = []
    for av_id, obs_info in observation_dict.items():
        skip_this_av = False
        av_info = obs_info['av']
        obs_df = obs_info['obs']
        av_edge_id = av_info['edge_id']
        av_edge_distance = av_info['lane_dis']
        av_speed = av_info['speed']
        if av_speed < transition_speed_threshold:
            skip_this_av = True

        rear_distance = ctm_link.cell_length
        front_distance = ctm_link.cell_length * 3
        if av_edge_id == ctm_link.link_id:
            # print('vehicle from the same direction')
            obs_min_dis = av_edge_distance - rear_distance
            obs_max_dis = av_edge_distance + front_distance
            if av_speed < stop_threshold:
                stop_locations.append(av_edge_distance)
            if av_speed > free_flow_threshold:
                free_flow_locations.append(av_edge_distance)
            same_direction = True
        else:
            av_edge_distance = 300 - av_edge_distance
            # print('vehicle from the opposite direction')
            obs_max_dis = av_edge_distance + rear_distance
            obs_min_dis = av_edge_distance - front_distance
            same_direction = False

        start_dis = max(obs_min_dis, 0)
        end_dis = min(obs_max_dis, ctm_link.length)

        observation_matrix, observation_diagonals = \
            obs_utils.get_observation_matrix(start_dis=start_dis,
                                             end_dis=end_dis,
                                             ctm_link=ctm_link)

        if cv_mode:
            obs_df = None            # fixme: add this line to ignore the av observation
        if obs_df is not None:
            truncated_obs_df = obs_df.loc[(obs_df.lane_dis >= start_dis) &
                                          (obs_df.lane_dis <= end_dis)]
            stopped_df = truncated_obs_df.loc[truncated_obs_df.speed < stop_threshold]
            vehicle_average_speed = truncated_obs_df['speed'].tolist()
            if len(vehicle_average_speed) > 0:
                average_speed = np.average(vehicle_average_speed)
                if not same_direction:
                    if average_speed < 5:
                        skip_this_av = True
            stop_locations += stopped_df['lane_dis'].tolist()
            free_flow_df = truncated_obs_df.loc[truncated_obs_df.speed > free_flow_threshold]
            free_flow_locations += free_flow_df['lane_dis'].tolist()
        else:
            truncated_obs_df = None

        if av_speed < free_flow_threshold:
            continue
        if same_direction:
            av_location = av_edge_distance
        else:
            av_location = None
        obs_mean, obs_variance = \
            _get_obs_mean_variance(truncated_obs_df, av_location,
                                   start_dis, end_dis, ctm_link, observation_diagonals)
        # obs_mean[0, 0] += same_direction
        if not skip_this_av:
            obs_location_dict[av_id] = {'h': observation_matrix, 'm': obs_mean, 'v': obs_variance}

    free_flow_event = get_free_flow_event(free_flow_locations, ctm_link)
    stop_event_dict = get_stop_event_model(stop_locations, red_light, ctm_link, 50)
    utilized_events = {}
    if free_flow_events:
        utilized_events.update(free_flow_event)
    if stop_events:
        utilized_events.update(stop_event_dict)
    if av_observations:
        if not cv_mode:
            utilized_events.update(obs_location_dict)
    return utilized_events


def _get_obs_mean_variance(obs_df, av_location, start_dis, end_dis, ctm_link, obs_diagonals):
    """
    get the observation mean and covariance given the observation and av location

    :param obs_df:
    :param av_location:
    :param start_dis:
    :param end_dis:
    :param ctm_link:
    :param obs_diagonals:
    :return:
    """
    start_cell_index = int(start_dis / ctm_link.cell_length)
    observed_cells = len(obs_diagonals)
    cell_length = ctm_link.cell_length
    variance_epsilon = 0.05

    mean_vec = [0 for _ in range(observed_cells)]
    covariance_diagonal = [variance_epsilon * (idx * idx / 2 + 1) / obs_diagonals[idx]
                           for idx in range(observed_cells)]
    covariance_diagonal = [val * val for val in covariance_diagonal]
    covariance_sub_diagonal = [0 for _ in range(observed_cells - 1)]

    if obs_df is None:
        observation_list = []
    else:
        observation_list = obs_df.to_dict('records')
    if av_location is not None:
        observation_list.append({'lane_dis': av_location, 'radius': 0})

    for obs_info in observation_list:
        vehicle_location = obs_info['lane_dis']
        radius = obs_info['radius']
        half_width = _get_vehicle_variance_width(radius)
        vehicle_start_dis = np.clip(vehicle_location - half_width, start_dis, end_dis)
        vehicle_end_dis = np.clip(vehicle_location + half_width, start_dis, end_dis - 0.0001)
        vehicle_start_idx = int(vehicle_start_dis / cell_length) - start_cell_index
        vehicle_end_idx = int(vehicle_end_dis / cell_length) - start_cell_index

        if vehicle_start_idx == vehicle_end_idx:
            mean_vec[vehicle_start_idx] += 1
        elif vehicle_end_idx - vehicle_start_idx == 1:
            boundary_location = int(vehicle_end_dis / cell_length) * cell_length
            first_part = boundary_location - vehicle_start_dis

            second_part = vehicle_end_dis - boundary_location

            first_portion = first_part / 2 / half_width
            second_portion = second_part / 2 / half_width

            variance = first_portion * second_portion
            mean_vec[vehicle_start_idx] += first_portion * obs_diagonals[vehicle_start_idx]
            mean_vec[vehicle_end_idx] += second_portion * obs_diagonals[vehicle_end_idx]
            covariance_diagonal[vehicle_start_idx] += variance
            covariance_diagonal[vehicle_end_idx] += variance
            covariance_sub_diagonal[vehicle_start_idx] -= variance
        else:
            exit('The width of the observation error cannot exceed the cell length')
    mean_vec = np.array([mean_vec]).T
    covariance_matrix = _get_covariance_matrix(covariance_diagonal, covariance_sub_diagonal) * 5
    return mean_vec, covariance_matrix


def _get_covariance_matrix(diagonals, sub_diagonals):
    covariance = np.zeros((len(diagonals), len(diagonals)))
    for idx in range(len(diagonals)):
        covariance[idx, idx] = diagonals[idx]
    for idx in range(len(sub_diagonals)):
        covariance[idx, idx + 1] = sub_diagonals[idx]
        covariance[idx + 1, idx] = sub_diagonals[idx]
    return covariance


def _get_vehicle_variance_width(radius):
    half_width = np.clip((radius / 3) ** 0.5 + 1, 3, 9.99 / 2)
    return half_width


if __name__ == '__main__':
    import matplotlib.pyplot as plt

    x_list = np.linspace(0, 100, 100)
    y_list = [_get_vehicle_variance_width(val) for val in x_list]
    plt.figure()
    plt.plot(x_list, y_list)
    plt.show()
