import os
from tqdm import tqdm
import mtldp.utils as mtlutils
import mtldp.mtltrajs as mtltrajs
import mtlimg.img_classes as img

timezone = "US/Eastern"
output_folder = "peachtree"


# load data from either traffic matrices or trajectory points
def generate_road_img_dict(network, overall_trajs_dict, start_tod, end_tod,
                           temporal_interval, distance_interval, map_layer="links"):
    """

    :param network:
    :param overall_trajs_dict:
    :param start_tod:
    :param end_tod:
    :param temporal_interval:
    :param distance_interval:
    :param map_layer:
    :return:
    """
    groupby_kwd = "link_id" if map_layer == "links" else "movement_id"
    points_df = overall_trajs_dict.get_points_df()
    points_df = mtlutils.df_add_date_time_and_tod(points_df, attr="timestamp", timezone_name=timezone)
    date_trajs_df = dict(tuple(points_df.groupby(["date"])))
    for date, daily_trajs_df in tqdm(date_trajs_df.items()):
        print(f"Processing {date}...")
        overall_points = mtltrajs.OverallPoints()
        overall_points.load_data(daily_trajs_df)
        road_trajs_dict = overall_points.get_trajs_dict(groupby='traj_id',
                                                        traj_attributes=['link_id', 'movement_id'])
        road_trajs_dict = road_trajs_dict.groupby(groupby_kwd)
        daily_road_img_dict = img.RoadImageDict(start_tod, end_tod, [date], temporal_interval, distance_interval,
                                                map_layer, timezone_name=timezone, city_id="peachtree")
        daily_road_img_dict.init_from_trajs_dict(road_trajs_dict, network)
        if not os.path.exists(output_folder):
            os.mkdir(output_folder)
        daily_road_img_dict.to_json(os.path.join(output_folder, f"{date}_traffic_image.json"))


def aggregate_road_image_dicts(road_dict_list):
    """

    :param road_dict_list: list of RoadImageDict
    :return: RoadImageDict
    """
    aggregated_road_image_dict = img.assign_weights_to_rimg_dicts(road_dict_list, weights=1.0 / len(road_dict_list))
    return aggregated_road_image_dict


def _get_time_columns(start_tod, end_tod, interval):
    start_date_time = mtlutils.tod_to_date_time(start_tod)
    end_date_time = mtlutils.tod_to_date_time(end_tod)
    time_columns = mtlutils.get_date_time_range(start_date_time, end_date_time,
                                                minute_interval=interval / 60, date_time_format="%H:%M:%S")
    return time_columns


if __name__ == "__main__":
    import pandas as pd
    import mtldp.mtlmap as mtlmap

    img_start_tod = 6
    img_end_tod = 22
    time_interval = 60
    distance_interval = 20
    layer = "links"

    network = mtlmap.build_network_from_xml(region_name='peachtree',
                                            file_name='peachtree/peachtree_filtered.osm',
                                            mode=mtlmap.MapMode.ACCURATE)

    points = pd.read_csv('peachtree/matched_trajs.csv')
    points_table = mtltrajs.OverallPoints()
    points_table.load_data(points)
    trajs_dict = points_table.get_trajs_dict(groupby='traj_id',
                                             traj_attributes=['link_id', 'movement_id', 'junction_id'])
    generate_road_img_dict(network, trajs_dict, img_start_tod, img_end_tod,
                           time_interval, distance_interval, map_layer=layer)
    # exit()

    # rdimg_dict = img.read_road_image_dict_from_json(os.path.join(output_folder, "1970-01-14_traffic_image.json"))
    #
    # arterial_info_dict = {"S": ['2390850312', '69488055'],
    #                       "N": ['69488055', '2390850312']}
    # corridor = mtlmap.Arterial(network, 'peachtree',
    #                            input_dict=arterial_info_dict, putin_network=True,
    #                            ref_node='69421277')
    # date_time_list = ["06:10", "06:20"]
    #
    # road_id_list = []
    # for oneway in corridor.oneways.values():
    #     if layer == "links":
    #         road_id_list = [str(link) for link in oneway.link_list]
    #     else:
    #         road_id_list = [str(movement) for movement in oneway.movement_list]
    #     break
    #
    # density_matrix = rdimg_dict.get_path_density(road_id_list, remove_incomplete_cell=True)
    # speed_matrix = rdimg_dict.get_path_speed(road_id_list, remove_incomplete_cell=True)
    # flow_matrix = rdimg_dict.get_path_flow(road_id_list, remove_incomplete_cell=True)
    #
    # # todo: start tod, end tod, interval, get time columns
    #
    # app_start_tod = 7.0
    # app_end_tod = 8.0
    # app_interval = 20
    #
    # app_time_columns = _get_time_columns(app_start_tod, app_end_tod, app_interval)
    #
    # for time_point in app_time_columns:
    #     for road_id in road_id_list:
    #         density_vector = rdimg_dict.get_density_vector(road_id, time_point, remove_incomplete_cell=True)
    #         speed_vector = rdimg_dict.get_speed_vector(road_id, time_point, remove_incomplete_cell=True)
    #         flow_vector = rdimg_dict.get_flow_vector(road_id, time_point, remove_incomplete_cell=True)
    #         # print()
