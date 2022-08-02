import numpy as np
import pandas as pd
from ctm_network_adapter.ctm_adapter import CTMAdapter


def get_free_flow_event(free_flow_points, ctm_net):
    """

    :param free_flow_points:
    :param ctm_net:
    :return:
    """

    noise_span = 5
    overall_indicator_vec = np.zeros(ctm_net.cell_num)
    mean_indicator_vec = np.zeros(ctm_net.cell_num)
    var_indicator_vec = np.zeros(ctm_net.cell_num)
    for row in free_flow_points.itertuples(index=False):
        laneset_dis = row.laneset_dis
        ctm_link_id = row.laneset_id
        ctm_link = ctm_net.links[ctm_link_id]
        free_flow_location = laneset_dis + ctm_link.link_length

        fd_parameters = ctm_link.fd_parameter
        lane_number = ctm_link.lane_number
        free_flow_veh_number = fd_parameters.critical_density_start * ctm_link.cell_length

        half_free_dis = fd_parameters.get_distance_headway_given_speed(fd_parameters.free_flow) / 2

        loc_start = max(free_flow_location - half_free_dis, 0)
        loc_end = min(ctm_link.link_length, free_flow_location + half_free_dis)
        local_indicator, start_idx = get_observable_indicator_list(loc_start, loc_end, ctm_link)
        local_indicator = np.array([x / lane_number for x in local_indicator])
        overall_indicator_vec[start_idx:start_idx + len(local_indicator)] += np.array(local_indicator)
        mean_indicator_vec[start_idx:start_idx + len(local_indicator)] += np.array(local_indicator)*free_flow_veh_number
        var_indicator_vec[start_idx:start_idx + len(local_indicator)] += np.array(local_indicator)/free_flow_veh_number
    observation_matrix, _ = observation_matrix_from_indicator(overall_indicator_vec)
    obs_mean = mean_indicator_vec[mean_indicator_vec.nonzero()]
    obs_mean = np.transpose(obs_mean)
    obs_var = var_indicator_vec[var_indicator_vec.nonzero()]
    obs_var = [1/val * 0.2 for val in obs_var]
    covariance_matrix = np.diag(obs_var)
    if len(obs_mean) == 0:
        return {}
    else:
        return {'free': {'h': observation_matrix, 'v': covariance_matrix, 'm': obs_mean}}


# def get_covariance_matrix(mean_indicator):
#     """
#
#     :param mean_indicator:
#     :return:
#     """
#     fraction_dict = {}
#     fractions = mean_indicator.nonzero()
#     fractions_idx = np.array(fractions).reshape(-1)
#     fraction_list =
#     for i in range(len(fractions_idx)):
#
#


def get_stop_event(stop_points, ctm_net, upstream_cut_dis=50):
    """
    :param stop_points:
    :param ctm_net:
    :param upstream_cut_dis:
    :return:
    """
    overall_indicator_vec = np.zeros(ctm_net.cell_num)
    mean_indicator_vec = np.zeros(ctm_net.cell_num)
    var_indicator_vec = np.zeros(ctm_net.cell_num)
    noise_span = 5

    for row in stop_points.itertuples(index=False):
        lane_dis = row.laneset_dis
        ctm_link_id = row.laneset_id
        ctm_link = ctm_net.links[ctm_link_id]
        stop_location = lane_dis + ctm_link.link_length

        fd_parameters = ctm_link.fd_parameter
        lane_number = ctm_link.lane_number
        half_jam_headway = 1 / fd_parameters.jam_density / 2
        single_lane_jam_veh = fd_parameters.jam_density * ctm_link.cell_length

        start_dis = stop_location - half_jam_headway
        end_dis = stop_location + half_jam_headway

        loc_start = max(start_dis, 0)
        loc_end = min(ctm_link.link_length, end_dis)
        local_indicator, start_idx = get_observable_indicator_list(loc_start, loc_end, ctm_link)
        local_indicator = np.array([x / lane_number for x in local_indicator])
        overall_indicator_vec[start_idx:start_idx + len(local_indicator)] += np.array(local_indicator)
        mean_indicator_vec[start_idx:start_idx + len(local_indicator)] += np.array(local_indicator)*single_lane_jam_veh
        var_indicator_vec[start_idx:start_idx + len(local_indicator)] += single_lane_jam_veh - np.array(local_indicator)

    observation_matrix, _ = observation_matrix_from_indicator(overall_indicator_vec)
    observation_matrix = np.clip(observation_matrix, 0, 1)
    obs_mean = mean_indicator_vec[mean_indicator_vec.nonzero()]
    obs_mean = np.transpose(obs_mean)
    var_vec = var_indicator_vec[var_indicator_vec.nonzero()]
    obs_var = [0.01 + val/5 for val in var_vec]
    covariance_matrix = np.diag(obs_var)

    if len(obs_mean) == 0:
        return {}

    return {'stop': {'h': observation_matrix, 'm': obs_mean, 'v': covariance_matrix}}


def get_observable_vector(ctm_link, obs_dict):
    """
    generate the observable indicator vector

    :param ctm_link:
    :param obs_dict:
    :return:
    """
    obs_row_vec = np.zeros((1, ctm_link.cell_numbers))
    for obs_details in obs_dict.values():
        obs_matrix = obs_details['h']
        local_obs_row = np.sum(obs_matrix, axis=0)
        if obs_row_vec is None:
            obs_row_vec = local_obs_row
        else:
            obs_row_vec += local_obs_row
    obs_row_vec = np.clip(obs_row_vec, 0, 1)
    return obs_row_vec.T


def get_observation_matrix(start_dis, end_dis, ctm_link):
    """
    get the observation matrix and observation fractions from the start/end distance of a ctm link

    :param start_dis:
    :param end_dis:
    :param ctm_link:
    :return:
    """
    indicator_list = get_observable_indicator_list(start_dis, end_dis, ctm_link)
    obs_matrix, obs_fractions = observation_matrix_from_indicator(indicator_list)
    return obs_matrix, obs_fractions


def get_observable_indicator_list(start_dis, end_dis, ctm_link):
    """
    get the observable indicator vector given the start distance and end distance

    :param start_dis:
    :param end_dis:
    :param ctm_link:
    :return:
    """
    # truncate the start dis and end dis
    start_dis = max(0, start_dis)
    end_dis = min(ctm_link.link_length, end_dis)
    start_idx = ctm_link.get_first_cell().cell_index

    cell_length = ctm_link.cell_length
    total_cells = len(ctm_link.cell_dict)
    start_cell_idx = int(start_dis / cell_length)
    end_cell_idx = int(end_dis / cell_length)

    if total_cells == end_cell_idx:
        end_cell_idx -= 1
    if total_cells == start_cell_idx:
        start_cell_idx -= 1

    left_fraction = 1 - (start_dis - cell_length * start_cell_idx) / cell_length
    right_fraction = (end_dis - cell_length * end_cell_idx) / cell_length
    if right_fraction == 0:
        observed_cells = end_cell_idx - start_cell_idx
        right_fraction = 1
    else:
        observed_cells = end_cell_idx - start_cell_idx + 1

    if observed_cells <= 0:
        raise ValueError('Observation cell number should be greater than zero')
    elif observed_cells == 1:
        observable_list = [left_fraction + right_fraction - 1]
    else:
        observable_list = [left_fraction] + [1 for _ in range(observed_cells - 2)] + [right_fraction]
    left_zeros = [0 for _ in range(start_cell_idx)]
    right_zeros = [0 for _ in range(total_cells - observed_cells - start_cell_idx)]
    indicator_list = left_zeros + observable_list + right_zeros
    return indicator_list, start_idx


def get_mean_indicator(loc, ctm_link, variance_range):

    start_dis = loc - 1/2 * variance_range
    end_dis = loc + 1/2 * variance_range
    mean_indicator, start_idx = get_observable_indicator_list(start_dis, end_dis, ctm_link)

    return mean_indicator, start_idx


def observation_matrix_from_indicator(obs_indicator_list):
    """

    :param obs_indicator_list:
    :return:
    """
    observation_dim = len(obs_indicator_list)
    observation_matrix = np.zeros((0, observation_dim))
    observation_fractions = []
    for idx in range(observation_dim):
        obs_indicator = obs_indicator_list[idx]
        if obs_indicator == 0:
            continue
        left_zeros = [0 for _ in range(idx)]
        right_zeros = [0 for _ in range(observation_dim - idx - 1)]
        local_vector = left_zeros + [obs_indicator] + right_zeros
        local_vector = np.array([local_vector])
        observation_matrix = np.concatenate([observation_matrix, local_vector], axis=0)
        observation_fractions.append(obs_indicator)
    return observation_matrix, observation_fractions

def get_observation_events(obs_points, ctm_net):
    obs_points = obs_points[obs_points['observed'] == True]
    for row in obs_points.itertuples(index=False):
        lane_dis = row.laneset_dis
        ctm_link_id = row.laneset_id
        ctm_link = ctm_net.links[ctm_link_id]

        rear_distance = ctm_link.cell_length
        front_distance = ctm_link.cell_length * 3




if __name__ == "__main__":
    import cores.mtlmap as mtlmap
    from ctm import load_ctm
    stop_event = []

    traj = pd.read_csv('../peachtree/interpolated_trajs.csv')

    mtl_network = mtlmap.build_network_from_xml(region_name='peachtree',
                                                file_name='../peachtree/peachtree_filtered.osm',
                                                mode=mtlmap.MapMode.ACCURATE)
    ctm_network = load_ctm.load_ctm_network("../data/peachtree", cell_length=20, time_interval=1, sub_steps=10)
    adapter = CTMAdapter(ctm_network, mtl_network)
    adapted_traj = adapter.generate_adapted_points(traj)
    # free_flow_points = adapted_traj[adapted_traj['speed'] >= 12]
    # free_flow_dict = dict(tuple(free_flow_points.groupby('timestamp')))
    # for time, points in free_flow_dict.items():
    #     events = get_free_flow_event(points, ctm_network)
    #     free_flow_event.append(events)
    stop_points = adapted_traj[adapted_traj['speed'] <= 0.1]
    stop_dict = dict(tuple(stop_points.groupby('timestamp')))
    for time, points in stop_dict.items():
        events = get_stop_event(points, ctm_network)
        stop_event.append(events)

