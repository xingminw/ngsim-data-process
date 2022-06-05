def identify_stopbar_clearance(network):
    for movement_id, movement in network.movements.items():
        movement.stopbar_latitude_list = None
        movement.stopbar_longitude_list = None

        movement.clearance_latitude_list = None
        movement.clearance_longitude_list = None

        upstream_link = movement.upstream_link
        downstream_link = movement.downstream_link
        node = movement.node.node_id
        clearance_label = "clearance:" + node
        if clearance_label in downstream_link.segment_list[0].osm_tags:
            clearance_list = downstream_link.segment_list[0].osm_tags[clearance_label].split('|')
            lat_list = []
            lon_list = []
            for pt in clearance_list:
                coordinates = pt.split(',')
                lat_list.append(float(coordinates[0]))
                lon_list.append(float(coordinates[1]))
            movement.clearance_latitude_list = lat_list
            movement.clearance_longitude_list = lon_list
        stopbar_label = "stopbar:" + node + '_' + str(movement.index)
        if stopbar_label in upstream_link.segment_list[-1].osm_tags:
            stopbar_list = upstream_link.segment_list[-1].osm_tags[stopbar_label].split('|')
            lat_list = []
            lon_list = []
            for pt in stopbar_list:
                coordinates = pt.split(',')
                lat_list.append(float(coordinates[0]))
                lon_list.append(float(coordinates[1]))
            movement.stopbar_latitude_list = lat_list
            movement.stopbar_longitude_list = lon_list
    return network
