"""
common utilities and some constant
"""


class PrintColors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


MPH_TO_METERS_PER_SEC = 0.44704

DISPLAY_LANE_INTERVAL = 5
SEGMENT_SHIFT_RATIO = 1.8

warning_print_head = f"\033[93mWarning\033[0m:"
warning_colors = ["\033[93m", "\033[0m:"]

error_print_head = f"\033[91mError\033[0m:"
error_colors = ["\033[91m", "\033[0m:"]

dual_ring = [[[1, 2], [5, 6]], [[3, 4], [7, 8]]]

spat_mapping_dict = {
    "2089": 62551869, "2631": 62565682, "2581": 62578814,
    "2641": 2041276569, "2671": 62517097, "2109": 62515137,
    "2149": 62477925, "2099": 62551152, "2119": 62505052,
    "1873": 62500567, "1833": 62500824, "1823": 62606176,
    "1863": 767530322, "2611": 29311341, "3183": 62569631,
    "2651": 2198688201, "2601": 62609566, "2661": 62477237,
    "2079": 62484707, "1853": 62532012, "5723": 62474956,
    "2571": 62596831, "297": 62527484, "1361": 62497500,
    "3399": 62595450, "3339": 62537929, "6235": 62499087,
    "2887": 62491077, "2877": 62500690, "2867": 62564598,
    "3103": 62544183, "3113": 62544207, "1135": 62601699,
    "1843": 62477148, "2857": 62477006, "2827": 62492569,
    "5437": 62492552, "2335": 62542029, "623": 62553419,
    "5643": 62544938, "5131": 62500913, "6175": 68133453,
    "1803": 62479267, "5447": 62492529, "1165": 62487316,
    "5397": 62498526, "3083": 5344004318, "6215": 394353360,
    "5653": 62487350, "3359": 62601733, "1175": 62550570,
    "5743": 62498570, "5427": 62487326, "3153": 62519175,
    "1311": 62601711, "5387": 62487716, "5753": 62490523,
    "2129": 62515171, "5407": 62486090, "347": 62484815,
    "5683": 62486120
}

reverse_spat_mapping_dict = {}
for k, v in spat_mapping_dict.items():
    reverse_spat_mapping_dict[str(v)] = k

signal_movement_dict = {
    "movement1": {
        "movement_id": 1,
        "geo_dir": "W2N",
        "direction": "l",
        "name": "EBL"
    },
    "movement2": {
        "movement_id": 2,
        "geo_dir": "E2W",
        "direction": "s",
        "name": "WB"
    },
    "movement3": {
        "movement_id": 3,
        "geo_dir": "N2E",
        "direction": "l",
        "name": "SBL"
    },
    "movement4": {
        "movement_id": 4,
        "geo_dir": "S2N",
        "direction": "s",
        "name": "NB"
    },
    "movement5": {
        "movement_id": 5,
        "geo_dir": "E2S",
        "direction": "l",
        "name": "WBL"
    },
    "movement6": {
        "movement_id": 6,
        "geo_dir": "W2E",
        "direction": "s",
        "name": "EB"
    },
    "movement7": {
        "movement_id": 7,
        "geo_dir": "S2W",
        "direction": "l",
        "name": "NBL"
    },
    "movement8": {
        "movement_id": 8,
        "geo_dir": "N2S",
        "direction": "s",
        "name": "SB"
    },
    "movement9": {
        "movement_id": 9,
        "geo_dir": "E2N",
        "direction": "r",
        "name": "WBR"
    },
    "movement10": {
        "movement_id": 10,
        "geo_dir": "S2E",
        "direction": "r",
        "name": "NBR"
    },
    "movement11": {
        "movement_id": 11,
        "geo_dir": "W2S",
        "direction": "r",
        "name": "EBR"
    },
    "movement12": {
        "movement_id": 12,
        "geo_dir": "N2W",
        "direction": "r",
        "name": "SBR"
    },
    "movement13": {
        "movement_id": 13,
        "geo_dir": "N2N",
        "direction": "b",
        "name": "SBB"
    },
    "movement14": {
        "movement_id": 14,
        "geo_dir": "S2S",
        "direction": "b",
        "name": "NBB"
    },
    "movement15": {
        "movement_id": 15,
        "geo_dir": "W2W",
        "direction": "b",
        "name": "EBB"
    },
    "movement16": {
        "movement_id": 16,
        "geo_dir": "E2E",
        "direction": "b",
        "name": "WBB"
    }
}


def get_moving_direction(upstream_from_dir, downstream_from_dir):
    """
    Get moving direction by inputting moving direction

    :param upstream_from_dir: from_direction of the upstream movement
    :param downstream_from_dir: from_direction of the downstream movement
    :return:
    """
    for movement_info in signal_movement_dict.values():
        geo_dir = movement_info["geo_dir"]
        if geo_dir[0] == upstream_from_dir and geo_dir[-1] == \
                get_inverse_geo_dir(downstream_from_dir):
            return movement_info["direction"]
    return None


def get_inverse_geo_dir(from_dir):
    """
    Get the inverse geometric direction
    Note that the input MUST be one of "E", "S", "W", or "N"
    For example, if the input is "E", then the output will be "W"

    :param from_dir: str, "E/S/W/N"
    :return: str, "W/N/E/S"
    """
    if from_dir == "E":
        return "W"
    elif from_dir == "W":
        return "E"
    elif from_dir == "N":
        return "S"
    elif from_dir == "S":
        return "N"
    else:
        return None


def get_movement_id(geo_dir, turn_dir):
    """
    Get a list of movement information based on the given geometric direction and turning direction

    :param geo_dir: str, "E", "W",
    :param turn_dir: str, "l", "r", "s", "b"
    :return: list
    """
    movement_list = []
    for movement_id, movement in signal_movement_dict.items():
        for t_d in turn_dir:
            if movement["direction"] == t_d:
                if movement["geo_dir"][0] == geo_dir:
                    movement_list.append(movement["movement_id"])
    return movement_list


def generate_geo_heading_direction(heading):
    """
    Convert the geometric heading to geometric direction

    :param heading: float, heading of an object, heading must be in the range of [-180, 180]
    :return: str, direction of the object
    """
    if -45 < heading <= 45:
        return "W"
    elif 45 < heading <= 135:
        return "S"
    elif - 135 < heading <= -45:
        return "N"
    else:
        return "E"
