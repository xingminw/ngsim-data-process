import numpy as np
import matplotlib.pyplot as plt


class CTMAdapter(object):

    def __init__(self, ctm_net, mtl_net):
        self.ctm_net = ctm_net
        self.mtl_net = mtl_net

    def generate_adapted_points(self, points_df):

        adapted_points = points_df
        laneset_list = []
        laneset_dis_list = []
        cell_index_list = []
        for row in points_df.itertuples(index=False):
            movement_id = row.movement_id
            laneset_dis = row.distance
            movement = self.mtl_net.movements[movement_id]
            movement_lanesets = movement.laneset_list

            if laneset_dis > 0:
                cur_link = movement.downstream_link
                cur_segment = cur_link.segment_list[0]
                cur_laneset = cur_segment.laneset_list[0]
                laneset_id = cur_laneset.laneset_id
                laneset_dis = laneset_dis - cur_laneset.length
                ctm_link = self.ctm_net.links[laneset_id]
                cell_index = self._get_location_in_link(laneset_dis, ctm_link)
            else:

                if len(movement_lanesets) <= 1:
                    laneset_id = movement_lanesets[0].laneset_id
                    ctm_link = self.ctm_net.links[laneset_id]
                    cell_index = self._get_location_in_link(laneset_dis, ctm_link)
                else:
                    reversed_movement_lanesets = movement_lanesets[::-1]
                    sum_distance = 0
                    last_distance = 0
                    idx = 0
                    while abs(laneset_dis) > sum_distance:
                        last_distance = sum_distance
                        cur_laneset = reversed_movement_lanesets[idx]
                        sum_distance += cur_laneset.length
                        idx += 1
                    laneset_dis += last_distance
                    laneset_id = reversed_movement_lanesets[idx - 1].laneset_id
                    ctm_link = self.ctm_net.links[laneset_id]
                    cell_index = self._get_location_in_link(laneset_dis, ctm_link)

            laneset_list.append(laneset_id)
            laneset_dis_list.append(laneset_dis)
            cell_index_list.append(cell_index)
            print()

        adapted_points['laneset_dis'] = laneset_dis_list
        adapted_points['cell_idx'] = cell_index_list
        adapted_points['laneset_id'] = laneset_list

        return adapted_points

    @staticmethod
    def _get_location_in_link(lane_dis, ctm_link):
        cell_length = ctm_link.cell_length
        link_length = ctm_link.link_length
        cell_num = len(ctm_link.cell_dict)

        raw_cell_index = int((lane_dis + link_length) / cell_length)

        if raw_cell_index < cell_num:
            link_cell_index = raw_cell_index
        else:
            link_cell_index = raw_cell_index - 1

        cell_id = f'{ctm_link.link_id}-{link_cell_index}'
        ctm_cell = ctm_link.cell_dict[cell_id]
        cell_index = ctm_cell.cell_index

        return cell_index

    # def gps_plot(self):
    #     self._ctm_map_matching()
    #     points_by_time = dict(tuple(self.points_df.groupby('timestamp')))
    #     cell_num = self.ctm_net.cell_num
    #     for time, points in points_by_time.items():
    #         veh_num_vec = np.zeros((cell_num, 1))
    #         loc_list = list(points['cell_idx'])
    #         for loc in loc_list:
    #             veh_num_vec[loc, 0] += 1
    #         veh_time_space_mat = np.hstack((veh_time_space_mat, veh_num_vec))
    #
    #     plt.imshow(veh_time_space_mat,
    #                vmin=0, vmax=20 / 7,
    #                cmap="binary", aspect='auto',
    #                origin='lower')
    #     plt.yticks(np.arange(0, cell_num, 5), np.arange(0, 20 * cell_num, 100))
    #     plt.xlabel('Time/s')
    #     plt.ylabel('Distance/m')
    #     plt.gca().invert_yaxis()
    #     plt.title('S-direction arterial')
    #     plt.show()


if __name__ == "__main__":
    import pandas as pd
    import cores.mtlmap as mtlmap
    from ctm import load_ctm

    traj = pd.read_csv('../peachtree/interpolated_trajs.csv')

    mtl_network = mtlmap.build_network_from_xml(region_name='peachtree',
                                                file_name='../peachtree/peachtree_filtered.osm',
                                                mode=mtlmap.MapMode.ACCURATE)
    ctm_network = load_ctm.load_ctm_network("../data/peachtree", cell_length=20, time_interval=1, sub_steps=10)
    adapter = CTMAdapter(ctm_network, mtl_network)
    res = adapter.generate_adapted_points(traj)
    print()
