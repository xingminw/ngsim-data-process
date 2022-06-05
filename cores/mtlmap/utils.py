def get_movement_list(link_list):
    """
    Get a list of movements from a list of links

    :param link_list: list of links
    :return: list of movements
    """
    movement_list = []
    node_list = []
    for idx in range(len(link_list) - 1):
        link = link_list[idx]
        node = link.downstream_node
        node_list.append(node)
        movements = node.movement_list
        upstream_link_id = link.link_id

        link = link_list[idx + 1]
        downstream_link_id = link.link_id
        detect_movement = None
        for movement in movements:
            if movement.upstream_link.link_id == upstream_link_id:
                if movement.downstream_link.link_id == downstream_link_id:
                    detect_movement = movement.movement_id
                    break
        movement_list.append(detect_movement)

    # print(movement_list)
    return movement_list
