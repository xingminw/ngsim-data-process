class Geometry(object):
    """
    Class for longitude and latitude

    **Main Attributes**
        -``.lon``: list of longitudes
        -``.lat``: list of latitudes
    """

    def __init__(self, lon_ls=None, lat_ls=None):
        """

        :param lon_ls: list of longitudes
        :param lat_ls: list of latitudes
        """
        if lon_ls is None:
            self.lon = []
            self.lat = []
        self.lon = lon_ls
        self.lat = lat_ls

    def __len__(self):
        return len(self.lon)

    def __str__(self):
        """

        :return: str, "lon lat;lon lat; ... ;lon lat"
        """
        return self._geometry2string()

    def append(self, other, remove_first=True):
        if remove_first:
            self.lon += other.lon[1:]
            self.lat += other.lat[1:]
        else:
            self.lon += other.lon
            self.lat += other.lat

    def init_from_node_list(self, node_list):
        latitude_list = []
        longitude_list = []
        for node in node_list:
            latitude_list.append(node.latitude)
            longitude_list.append(node.longitude)
        self.lon = longitude_list
        self.lat = latitude_list
        return self

    def _geometry2string(self):
        """
        Convert the Geometry object to a string of "lon lat;lon lat; ... ;lon lat"

        :return: str
        """
        output = ""
        for i in range(len(self.lon) - 1):
            output += (str(self.lon[i]) + " " + str(self.lat[i]) + ";")
        output += (str(self.lon[-1]) + " " + str(self.lat[-1]))
        return output

    def geometry2list(self):
        """
        Convert the Geometry object to a list of [[lon1, lat1], [lon2, lat2], ...]

        :return: list
        """
        output = []
        for i in range(len(self.lon)):
            output.append([self.lon[i], self.lat[i]])
        return output


class BoundingBox(object):
    """
    Class for a region bounded by a given pair of geometric coordinates

    **Main Attributes**
        - ``.min_lon``: float, minimum longitude of the BoundingBox
        - ``.max_lon``: float, maximum longitude of the BoundingBox
        - ``.min_lat``: float, minimum latitude of the BoundingBox
        - ``.max_lon``: float, maximum latitude of the BoundingBox
    """

    def __init__(self, lon_1, lat_1, lon_2, lat_2, data_type=float):
        """

        :param lon_1:
        :param lat_1:
        :param lon_2:
        :param lat_2:
        :param data_type: target data type of the attributes
        """
        lon_1, lon_2 = data_type(lon_1), data_type(lon_2)
        lat_1, lat_2 = data_type(lat_1), data_type(lat_2)
        self.min_lon = min(lon_1, lon_2)
        self.max_lon = max(lon_1, lon_2)
        self.min_lat = min(lat_1, lat_2)
        self.max_lat = max(lat_1, lat_2)

    def boundingBox2list(self):
        """
        Convert the BoundingBox object to a list [min_lon, min_lat, max_lon, max_lat]

        :return: list
        """

        return [self.min_lon, self.min_lat, self.max_lon, self.max_lat]

    def get_bound_dict(self, value_type=float):
        """
        Convert the BoundingBox object to a dictionary
        Note that the keys are "maxlon", "minlon", "maxlat", and "minlat", the values are the corresponding attributes

        :param value_type: data type of the values of the returned dictionary
        :return: dict
        """
        return {"maxlon": value_type(self.max_lon), "minlon": value_type(self.min_lon),
                "maxlat": value_type(self.max_lat), "minlat": value_type(self.min_lat)}


def get_geometry_from_str(input_str):
    coordinate_pair_ls = input_str.split(";")
    lat_ls = []
    lon_ls = []
    for coord_pair in coordinate_pair_ls:
        coord_pair_ls = coord_pair.split(" ")
        lon_ls.append(float(coord_pair_ls[0]))
        lat_ls.append(float(coord_pair_ls[1]))
    return Geometry(lon_ls, lat_ls)


def get_bounding_box(attri, data_type=float):
    """
    Get BoundingBox object from a dictionary
    Note that the keys of attri must be "maxlon", "minlon", "maxlat", and "minlat"

    :param attri: dict
    :param data_type: data type of the attributes of the BoundingBox
    :return: `mtldp.utils.BoundingBox`
    """
    return BoundingBox(attri["maxlon"], attri["maxlat"], attri["minlon"], attri["minlat"], data_type)
