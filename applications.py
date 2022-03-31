# load data from either traffic matrices or trajectory points

# todo: get full image
density_matrix = img.get_path_density(road_list)
speed_matrix = img.get_path_speed(road_list)

time_list = [0, 1, 2, 3, 4]
# time_list = ['00:00', '00:02']
for i_time in time_list:
    link_id = "XXX"             # segment_id,...
    # todo: some functions to extract data from traffic images
    density_vector = img.get_density_vec(link_id, i_time)
    speed_vector = img.get_density_vec(link_id, i_time)
    cell_length_list = img.get_cell_length_list(link_id)
