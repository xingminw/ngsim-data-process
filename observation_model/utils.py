import numpy as np
import portion as itv
import random
from ctm_network_adapter.ctm_adapter import CTMAdapter


def get_polar_coordinates(x, y):
    """
    convert the coordinates into polar coordinates

    :param x:
    :param y:
    :return:
    """
    radius = np.sqrt(x * x + y * y)
    angle = np.degrees(np.arccos(x / radius))
    if abs(y) > 0:
        angle *= np.sign(y)
    return angle, radius


def get_vehicle_angle_interval(x, y, width, length):
    """
    get the occupied vehicle angle interval

    :param x:
    :param y:
    :param width:
    :param length:
    :return:
    """
    angle1, _ = get_polar_coordinates(x + length / 2, y + width / 2)
    angle2, _ = get_polar_coordinates(x + length / 2, y - width / 2)
    angle3, _ = get_polar_coordinates(x - length / 2, y + width / 2)
    angle4, _ = get_polar_coordinates(x - length / 2, y - width / 2)

    angle_min = min(angle1, angle2, angle3, angle4)
    angle_max = max(angle1, angle2, angle3, angle4)
    return itv.closed(angle_min, angle_max)


def size_of_interval(interval):
    if interval.empty:
        return 0

    total_duration = 0
    for sub_interval in interval._intervals:
        total_duration += sub_interval.upper - sub_interval.lower
    return total_duration


def get_automated_vehicle(trajs, penetration_rate):
    vehicles = trajs['veh_id'].unique()
    av_num = int(penetration_rate * len(vehicles))
    av_list = random.sample(list(vehicles), av_num)
    av_trajs = trajs[trajs['veh_id'].isin(av_list)]

    return av_list


if __name__ == '__main__':
    import matplotlib.pyplot as plt
    x = -1
    y = np.linspace(-1000, 1000, 1000)
    angle_list = [get_polar_coordinates(x, val)[0] for val in y]
    plt.figure()
    plt.plot(angle_list, y)
    plt.show()
