"""
Utility functions with regard to the GPS coordinates

The valid degree is within ``(-180, 180]``

Reference:

- Tutorial: http://www.movable-type.co.uk/scripts/latlong.html

"""

import math
import numpy as np

from . import constants as utils
from .geometry import Geometry


def haversine_distance(coord1: tuple, coord2: tuple):
    """
    Get the distance between two gps coordinates.

    :param coord1: GPS point 1 in tuple (lat, lon)
    :param coord2: GPS point 2 in tuple (lat, lon)
    :return:
        distance in meters
    """
    radius = 6372800  # Earth radius in meters
    lat1, lon1 = coord1
    lat2, lon2 = coord2

    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = math.sin(delta_phi / 2) ** 2 + \
        math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2

    return 2 * radius * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def get_trace_length(lat_list, lon_list):
    """
    Get the length of a trajectory data.

    :param lat_list: latitude list
    :param lon_list: longitude list
    :return: lengths of the trajectory by meters
    """
    total_lengths = 0
    if len(lat_list) != len(lon_list):
        print(utils.warning_print_head, "get trace distance input does not have equal dims")

    for idx in range(min(len(lat_list), len(lon_list)) - 1):
        total_lengths += haversine_distance((lat_list[idx], lon_list[idx]),
                                            (lat_list[idx + 1], lon_list[idx + 1]))
    return total_lengths


def get_directed_segment_heading(start_coord: tuple, end_coord: tuple):
    """
    Calculate the heading of a directed line segment.

    Use cosine approximation, if the distance between the two points is too large, then this will
    not give you the write output

    :param start_coord: GPS point 1 in tuple ``(lat, lon)``
    :param end_coord: GPS point 2 in tuple ``(lat, lon)``
    :return: heading from ``(-180, 180]``
    """
    if haversine_distance(start_coord, end_coord) > 10000:
        print(f"\033[93mWarning\033[0m:", "distance between two points too large when calculating their heading "
                                          "@ gps_utils.get_directed_segment_heading()")
    start_lat, start_lon = start_coord
    end_lat, end_lon = end_coord
    delta_y = end_lat - start_lat
    mean_lat = (start_lat + end_lat) / 2
    lon_scale = math.cos(mean_lat / 180 * math.pi)
    delta_x = (end_lon - start_lon) * lon_scale
    if delta_x != 0:
        approximated_heading = math.atan(delta_y / delta_x)
        approximated_degree = approximated_heading * 180 / math.pi

        if delta_x < 0:
            if delta_y < 0:
                approximated_degree -= 180
            elif delta_y > 0:
                approximated_degree += 180
            else:
                approximated_degree = 180
    else:
        if delta_y > 0:
            approximated_degree = 90
        else:
            approximated_degree = -90
    return approximated_degree


def reverse_degree(degree):
    """
    Get the reverse degree

    :param degree:
    :return:
    """
    if degree > 0:
        return degree - 180
    else:
        return degree + 180


def get_angle_difference(degree1: float, degree2: float):
    """
    Get the difference between two angle (the output is always less than 180)

    :param degree1:
    :param degree2:
    :return: difference of the two angles
    """
    delta_degree = degree1 - degree2
    if delta_degree > 180:
        delta_degree -= 360

    if delta_degree < -180:
        delta_degree += 360
    delta_degree = (delta_degree + 180) % 360 - 180
    return abs(delta_degree)


def get_closest_angle(degree, degree_list):
    """
    Get the closest angle (return the index) among a set of options.

    :param degree:
    :param degree_list:
    :return:
    """

    angle_diff = [get_angle_difference(degree, val) for val in degree_list]
    return int(np.argmin(angle_diff)), np.min(angle_diff)


def get_gps_trace_heading_info(lat_list, lon_list):
    """
    Get the heading angle given the lat and lon list.

    :param lat_list:
    :param lon_list:
    :return: forward_heading, forward_weighted_heading, backward_heading, backward_weighted_heading

    """

    if len(lat_list) < 2:
        return None, None, None, None

    if len(lat_list) != len(lon_list):
        print(utils.warning_print_head, "get trace distance input does not have equal dims")

    heading_list = []
    for idx in range(min(len(lat_list), len(lon_list)) - 1):
        start_lat = lat_list[idx]
        end_lat = lat_list[idx + 1]
        start_lon = lon_list[idx]
        end_lon = lon_list[idx + 1]
        heading = get_directed_segment_heading((start_lat, start_lon), (end_lat, end_lon))
        heading_list.append(heading)

    forward_heading = heading_list[-1]
    backward_heading = reverse_degree(heading_list[0])

    weight_list = [val + 1 for val in range(len(heading_list))]
    total_weight = sum(weight_list)

    forward_weighted_heading = \
        sum([weight_list[idx] * heading_list[idx] for idx in range(len(heading_list))]) / total_weight
    weight_list = weight_list[::-1]
    backward_weighted_heading = \
        sum([reverse_degree(heading_list[idx]) * weight_list[idx] for idx in range(len(heading_list))]) / total_weight
    return forward_heading, forward_weighted_heading, backward_heading, backward_weighted_heading


def segment_gps_trace(geometry, split_into=10):
    """
    Split the gps trace evenly.

    :param geometry:
    :param split_into:
    :return: list of Geometry
    """
    lat_list = geometry.lat
    lon_list = geometry.lon
    geometry_ls = []
    radius = 6372800  # Earth radius in meters
    total_distance = get_trace_length(lat_list, lon_list)
    unit_distance = total_distance / split_into
    num_segments = min(len(lat_list), len(lon_list)) - 1
    distance_arr = []
    for idx in range(num_segments):
        distance_arr.append(haversine_distance((lat_list[idx], lon_list[idx]), (lat_list[idx + 1], lon_list[idx + 1])))
    # segment_lat_list = []
    # segment_lon_list = []
    current_segment = 0
    previous_lat = lat_list[0]
    previous_lon = lon_list[0]
    for i in range(split_into):
        current_lat_list = [previous_lat]
        current_lon_list = [previous_lon]
        current_distance = haversine_distance((previous_lat, previous_lon),
                                              (lat_list[current_segment + 1], lon_list[current_segment + 1]))
        while current_distance - unit_distance < -1e-3:
            current_lat_list.append(lat_list[current_segment + 1])
            current_lon_list.append(lon_list[current_segment + 1])
            current_segment += 1
            current_distance += distance_arr[current_segment]

        fraction = ((i + 1) * unit_distance - sum(distance_arr[segment] for segment in range(current_segment))) \
                   / distance_arr[current_segment]
        delta = distance_arr[current_segment] / radius
        a, b = math.sin((1 - fraction) * delta) / math.sin(delta), math.sin(fraction * delta) / math.sin(delta)
        phi1, phi2 = math.radians(lat_list[current_segment]), math.radians(lat_list[current_segment + 1])
        lambda1, lambda2 = math.radians(lon_list[current_segment]), math.radians(lon_list[current_segment + 1])
        x = a * math.cos(phi1) * math.cos(lambda1) + b * math.cos(phi2) * math.cos(lambda2)
        y = a * math.cos(phi1) * math.sin(lambda1) + b * math.cos(phi2) * math.sin(lambda2)
        z = a * math.sin(phi1) + b * math.sin(phi2)
        phi_i = math.atan2(z, math.sqrt(math.pow(x, 2) + math.pow(y, 2)))
        lambda_i = math.atan2(y, x)
        lat, lon = math.degrees(phi_i), math.degrees(lambda_i)

        current_lat_list.append(lat)
        current_lon_list.append(lon)
        # segment_lat_list.append(current_lat_list)
        # segment_lon_list.append(current_lon_list)
        segment_geometry = Geometry(current_lon_list, current_lat_list)
        geometry_ls.append(segment_geometry)
        previous_lat, previous_lon = lat, lon

    return geometry_ls


def shift_geometry(geometry, shift_distance: float = 7, shift_direction: str = "left"):
    """
    Shift the geometry towards a certain direction.

    :param geometry: `mtldp.utils.Geometry`
    :param shift_distance: meters
    :param shift_direction: ``"left"`` or ``"right"``
    :return:
    """
    lat_list = geometry.lat
    lon_list = geometry.lon
    heading, _, _, _ = get_gps_trace_heading_info(lat_list, lon_list)
    if heading <= 0 and shift_direction == "left":
        [shifted_lat_list, shifted_lon_list] = get_shifted_gps_trace(lat_list, lon_list, -heading, shift_distance)
    elif heading <= 0 and shift_direction == "right":
        [shifted_lat_list, shifted_lon_list] = get_shifted_gps_trace(lat_list, lon_list, -heading + 180, shift_distance)
    elif heading > 0 and shift_direction == "left":
        [shifted_lat_list, shifted_lon_list] = get_shifted_gps_trace(lat_list, lon_list, 360 - heading, shift_distance)
    elif heading > 0 and shift_direction == "right":
        [shifted_lat_list, shifted_lon_list] = get_shifted_gps_trace(lat_list, lon_list, 180 - heading, shift_distance)
    else:
        print(utils.warning_print_head, "shift geometry not correct @", __name__, shift_geometry.__name__)
        [shifted_lat_list, shifted_lon_list] = [[], []]
    return Geometry(shifted_lon_list, shifted_lat_list)


def get_shifted_gps_trace(lat_list, lon_list, shift_direction=0.0, shift_distance: float = 20):
    """
    Shift the GPS trace towards a certain direction.

    :param lat_list:
    :param lon_list:
    :param shift_direction: shifting direction given by angle
    :param shift_distance:
    :return:
    """
    radius = 6372800  # Earth radius in meters
    if len(lat_list) != len(lon_list):
        print(utils.warning_print_head, "get shifted gps trace input does not have equal dims")

    shifted_lat_list = []
    shifted_lon_list = []
    for idx in range(min(len(lat_list), len(lon_list))):
        lat, lon = lat_list[idx], lon_list[idx]
        phi1, lambda1 = math.radians(lat), math.radians(lon)
        delta = shift_distance / radius
        theta = math.radians(shift_direction)

        phi2 = math.asin(
            math.sin(phi1) * math.cos(delta) + math.cos(phi1) * math.sin(delta) * math.cos(theta))
        lambda2 = lambda1 + math.atan2(math.sin(theta) * math.sin(delta) * math.sin(phi1),
                                       math.cos(delta) - math.sin(phi1) * math.sin(phi2))

        shifted_lat, shifted_lon = math.degrees(phi2), math.degrees(lambda2)
        shifted_lat_list.append(shifted_lat)
        shifted_lon_list.append(shifted_lon)

    return [shifted_lat_list, shifted_lon_list]


if __name__ == '__main__':
    pass
