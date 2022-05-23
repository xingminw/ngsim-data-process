import pandas as pd
import matplotlib.pyplot as plt
import mtldp.mtlmap as mtlmap
import mtldp.mtltrajs as mtltrajs
import mtldp.mobility_utils as mtlmobility


network = mtlmap.build_network_from_xml(region_name='peachtree',
                                        file_name='peachtree/peachtree_filtered.osm',
                                        mode=mtlmap.MapMode.ACCURATE)

# adding arterial
arterial_info_dict = {"S": ['2390850312', '69488055'],
                      "N": ['69488055', '2390850312']}
corridor = mtlmap.Arterial(network, 'peachtree',
                           input_dict=arterial_info_dict, putin_network=True,
                           ref_node='69421277')

points_df = pd.read_csv('peachtree/matched_trajs.csv')
points_table = mtltrajs.OverallPoints()

points_table.load_data(points_df)
trajs_dict = points_table.get_trajs_dict(groupby='traj_id',
                                         traj_attributes=['link_id', 'movement_id', 'junction_id'])
movement_trajs_dict = trajs_dict.groupby('movement_id')

# todo: load spat data

for oneway in corridor.oneways.values():
    fig, ax = plt.subplots()
    flip_figure = False
    if oneway.direction in ['S', 's', 'W', 'w']:
        flip_figure = True
    print(oneway.direction)
    # todo: add plots here
    # ax.plot(x_list, y_list, color='g')
    mtlmobility.plot_path_ts(ax, oneway, movement_trajs_dict, flip=flip_figure)
    distance_dict = oneway.distance_by_node
    print(distance_dict)
    plt.savefig(f"output/{oneway.direction}.png", dpi=300)
    # plt.show()
    plt.close()
