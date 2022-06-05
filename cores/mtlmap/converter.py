import os
import osmnx as ox


def convert_osm_to_shp(osm_file, output_folder, fastmm=True,
                       bidirectional=False, simplify=False, retain_all=True,
                       encoding="utf-8") -> None:
    """
    Convert the OSM xml map to shapefile

    This function requires the osmnx package

    Reference:

    - OSMnx (https://github.com/gboeing/osmnx)
    - OSMnx example (https://github.com/gboeing/osmnx-examples)

    :param osm_file: str, path of the file
    :param output_folder: str, path of the folder for output
    :param fastmm: True to output the shapefile for the fast map matching
    :param bidirectional: bool, True if the user wants to have bidirectional format, default False
    :param simplify: bool, True if the user wants to simplify the result, default False
    :param retain_all:
    :param encoding: str, default "utf-8"
    :return: None
    """
    graph = ox.graph_from_xml(osm_file, bidirectional=bidirectional, simplify=simplify, retain_all=retain_all)

    if not os.path.exists(output_folder):
        os.mkdir(output_folder)

    if fastmm:
        nodes_file = os.path.join(output_folder, "nodes.shp")
        edges_file = os.path.join(output_folder, "edges.shp")

        gdf_nodes, gdf_edges = ox.graph_to_gdfs(graph)
        gdf_nodes = ox.io._stringify_nonnumeric_cols(gdf_nodes)
        gdf_edges = ox.io._stringify_nonnumeric_cols(gdf_edges)

        if not os.path.exists(nodes_file):
            gdf_nodes.to_file(nodes_file, encoding=encoding)
        if not os.path.exists(edges_file):
            gdf_edges.to_file(edges_file, encoding=encoding)
    else:
        ox.save_graph_shapefile(graph, output_folder)
