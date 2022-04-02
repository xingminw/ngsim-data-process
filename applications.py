import os
from tqdm import tqdm
import mtldp.utils as mtlutils
import mtldp.mtltrajs as mtltrajs
import mtlimg.img_classes as img

timezone = "US/Eastern"
output_folder = os.path.join("output", "traffic_images")


# load data from either traffic matrices or trajectory points
def generate_road_img_dict(network, overall_trajs_dict, start_tod, end_tod,
                           temporal_interval, distance_interval, map_layer="links"):
    groupby_kwd = "link_id" if map_layer == "links" else "movement_id"
    points_df = overall_trajs_dict.get_points_df(attributes="all")
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
        date_road_dict[date] = img.read_road_image_dict_from_json(os.path.join(output_folder, file_name))

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

    for road_id in road_id_list:
        for time_point in time_list:
            density_vector = rdimg_dict.get_density_vector(road_id, time_point, remove_incomplete_cell=True)
            speed_vector = rdimg_dict.get_speed_vector(road_id, time_point, remove_incomplete_cell=True)
            flow_vector = rdimg_dict.get_flow_vector(road_id, time_point, remove_incomplete_cell=True)


if __name__ == "__main__":
    import pandas as pd
    import mtldp.mtlmap as mtlmap

    start_tod = 6
    end_tod = 22
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
    # generate_road_img_dict(network, trajs_dict, start_tod, end_tod,
    #                        time_interval, distance_interval, map_layer=layer)

    date_rdimg_dict = load_road_img_dict()

    arterial_info_dict = {"S": ['2390850312', '69488055'],
                          "N": ['69488055', '2390850312']}
    corridor = mtlmap.Arterial(network, 'peachtree',
                               input_dict=arterial_info_dict, putin_network=True,
                               ref_node='69421277')
    date_time_list = ["06:10", "06:20"]

    for date, rdimg_dict in date_rdimg_dict.items():
        for oneway in corridor.oneways.values():
            if layer == "links":
                road_id_list = [str(link) for link in oneway.link_list]
            else:
                road_id_list = [str(movement) for movement in oneway.movement_list]
            application(rdimg_dict, road_id_list, date_time_list)



    print()
