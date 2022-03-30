import os
import json
import mtldp.mtlmap as mtlmap


network = mtlmap.build_network_from_xml(region_name='peachtree',
                                        file_name='peachtree/peachtree_filtered.osm',
                                        mode=mtlmap.MapMode.ACCURATE)

# adding arterial
arterial_info_dict = {"S": ['2390850312', '69488055'],
                      "N": ['69488055', '2390850312']}
mtlmap.Arterial(network, 'peachtree',
                input_dict=arterial_info_dict, putin_network=True,
                ref_node='69421277')

# output map folder
map_output_folder = 'output/map_files'
if not os.path.exists(map_output_folder):
    os.mkdir(map_output_folder)

bbox = network.bounds.get_bound_dict()
bbox_text = json.dumps(bbox, indent=2)
# save bounding box
with open(f'{map_output_folder}/bbox.json', 'w') as temp_file:
    temp_file.write(bbox_text)

map_output_csv = f'{map_output_folder}/csv'
if not os.path.exists(map_output_csv):
    os.mkdir(map_output_csv)
mtlmap.output_static_geometry_json(network, f'{map_output_folder}/peachtree.json')
mtlmap.save_network_to_csv(network, map_output_csv)

# output shapefiles
directed_osm_file = f'{map_output_folder}/directed.osm'
mtlmap.save_network_to_xml(network, directed_osm_file,
                           directed=True)
mtlmap.convert_osm_to_shp(directed_osm_file,
                          f'{map_output_folder}/shp', fastmm=True)
print()
