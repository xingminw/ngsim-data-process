import os
import mtldp.utils as mtlutils
import mtltrajs as mtltrajs
import mtlimg.img_classes as img

timezone = "US/Eastern"
output_folder = "output/traffic_images"


# load data from either traffic matrices or trajectory points
def generate_road_img_dict(network, overall_trajs_dict, start_tod, end_tod,
                           temporal_interval, distance_interval, groupby_kwd="links"):
    points_df = overall_trajs_dict.get_points_df(attributes="all")
    points_df = mtlutils.df_add_date_time_and_tod(points_df, attr="timestamp", timezone_name=timezone)
    date_trajs_df = dict(tuple(points_df.groupby(["date"])))
    for date, daily_trajs_df in date_trajs_df.items():
        print(f"Processing {date}...")
        overall_points = mtltrajs.OverallPoints(df=daily_trajs_df)
        daily_trajs_dict = overall_points.get_trajs_dict()
        road_trajs_dict = daily_trajs_dict.groupby(groupby_kwd)
        daily_road_img_dict = img.RoadImageDict(start_tod, end_tod, [date], temporal_interval, distance_interval,
                                                groupby_kwd,
                                                timezone_name=timezone, city_id="peachtree")
        daily_road_img_dict.init_from_trajs_dict(road_trajs_dict, network)
        if not os.path.exists(output_folder):
            os.mkdir(output_folder)

        daily_road_img_dict.to_json(os.path.join(output_folder, f"output/{date}_traffic_image"))


def load_road_img_dict():
    """

    :return: `dict`, {date: RoadImageDict}
    """
    date_road_dict = {}
    if not os.path.exists(output_folder):
        print(f"No data found in {output_folder}")
        return None

    file_name_list = os.listdir(output_folder)
    for file_name in file_name_list:
        date = file_name.split("_")[0]
        date_road_dict[date] = img.read_road_image_dict_from_json(file_name)

    return date_road_dict


def aggregate_road_image_dicts(road_dict_list):
    """

    :param road_dict_list: list of RoadImageDict
    :return: RoadImageDict
    """
    aggregated_road_image_dict = img.assign_weights_to_rimg_dicts(road_dict_list, weights=1.0 / len(road_dict_list))
    return aggregated_road_image_dict


def application(rdimg_dict, road_id_list, time_list):
    """

    :param rdimg_dict: list of RoadImageDict
    :param road_id_list: list of road_id
    :param time_list: list of date time string
    :return:
    """
    density_matrix = rdimg_dict.get_path_density(road_id_list, remove_incomplete_cell=True)
    speed_matrix = rdimg_dict.get_path_speed(road_id_list, remove_incomplete_cell=True)
    flow_matrix = rdimg_dict.get_path_flow(road_id_list, remove_incomplete_cell=True)

    for road_id, road_image in rdimg_dict.dict.items():
        for time_point in time_list:
            density_vector = road_image.get_density_vector(road_id, time_point, remove_incomplete_cell=True)
            speed_vector = road_image.get_speed_vector(road_id, time_point, remove_incomplete_cell=True)
            flow_vector = road_image.get_flow_vector(road_id, time_point, remove_incomplete_cell=True)

if __name__ == "__main__":
    pass