import numpy as np
import pandas as pd
from pyproj import Transformer
from mtldp.adapters.adapter_base import TrajectoryAdapterBase


class NgsimTrajectoryAdapter(TrajectoryAdapterBase):
    def __init__(self):
        self.dtype_dict = {'Vehicle_ID': str}

        self.attribute_map = {'Vehicle_ID': 'veh_id',
                              'v_Vel': 'speed'}

    def load(self, file_list: list):
        df_list = []
        feet2meter = 0.3048
        # 'epsg:2240' is for Georgia West State Plane in NAD83
        trans = Transformer.from_crs('epsg:2240', 'epsg:4326')
        for file in file_list:
            df = pd.read_csv(file, dtype=self.dtype_dict)
            df = df.rename(columns=self.attribute_map)
            df = df.sort_values(by=['veh_id', 'Global_Time'])
            df = df.drop(columns=[])
            df['timestamp'] = df['Global_Time'] * 0.001
            global_x_list = df['Global_X']
            global_y_list = df['Global_Y']

            gps_x_list = []
            gps_y_list = []
            for (x, y) in zip(global_x_list, global_y_list):
                gps_x, gps_y = trans.transform(x, y)
                gps_x_list.append(gps_x)
                gps_y_list.append(gps_y)
            df['longitude'] = gps_y_list
            df['latitude'] = gps_x_list
            df['speed'] = df['speed'] * feet2meter
            df_list.append(df)
        df_combine = pd.concat(df_list, ignore_index=True)
        df_combine['trip_id'] = df_combine['veh_id']
        return df_combine
