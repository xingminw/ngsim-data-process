import pandas
import pandas as pd

laneset_raw = pd.read_csv('D:/osm-map-parser/output/peachtree/lanesets.csv')
laneset_raw['sat_flow'] = laneset_raw['lane_number'] * 1800
laneset_raw['jam_density'] = 7
laneset_raw['shockwave'] = 5
laneset = laneset_raw[['laneset_id', 'length', 'speed_limit', 'lane_number', 'shockwave', 'jam_density', 'sat_flow']]
laneset = laneset.rename(columns={'laneset_id': 'link_id', 'length': 'link_length', 'speed_limit': 'free_v'})
laneset.to_csv('calibration/links.csv', index=None)

