"""

main features:

* Conversion between the timestamp and the date time considering the different timezone
* get the yyyy-mm-dd and hh:mm:ss or hh:mm 7.2

We have three types of time
1. timestamp                -       'timestamp'
2. numpy.datetime64[ns]     -       'dt'
3. tod float                -       'tod'

add a global variable to store the strfmt
4. date                     -       'date': 'yyyy-mm-dd'
5. datetime                 -       'date_time': 'hh:mm'

Two general types:

* single time
* time in df

* add the 'tod' (between 0 and 24) so that
* Time of Day (TOD) and TOD interval: example: [7, 10], etc.
* Filter data according to different TOD

Solutions:

Main classes and member functions

TimeZone (already there)

datetime?

TodInterval

Utility functions
"""
import numpy as np
import pandas as pd

DATE_FORMAT = "%Y-%m-%d"
DATE_TIME_FORMAT = "%H:%M"
DEFAULT_TIMEZONE = "UTC"


def df_add_date_time_and_tod(df, attr="timestamp", timezone_name=DEFAULT_TIMEZONE, tod_column_name="tod",
                             date_column_name="date", date_time_column_name="date_time", date_format=DATE_FORMAT,
                             date_time_format=DATE_TIME_FORMAT):
    """
    Add date and tod to DataFrame
    Note that if the user want the column of date to be np.datetime64, please run the following:
            df[date_column_name] = pd.to_datetime(df[attr], unit='s', utc=True)
            df[date_column_name] = df['attr'].dt.tz_convert(tz=tod_column_name)
    """
    if not (attr in ['timestamp']):
        raise NotImplementedError
    df = df_add_date(df, attr=attr, date_column_name=date_column_name,
                     date_format=date_format, timezone_name=timezone_name)
    df = df_add_tod(df, attr=attr, tod_column_name=tod_column_name, timezone_name=timezone_name)
    df = df_add_date_time(df, attr=attr, date_time_column_name=date_time_column_name,
                          date_time_format=date_time_format, timezone_name=timezone_name)
    return df


def df_add_date(df, attr="timestamp", date_column_name="date", date_format=DATE_FORMAT, timezone_name=DEFAULT_TIMEZONE):
    if not (attr in ['timestamp']):
        raise NotImplementedError
    df[date_column_name] = pd.to_datetime(df[attr], unit='s', utc=True).dt.tz_convert(tz=timezone_name)
    df[date_column_name] = df[date_column_name].dt.strftime(date_format)
    return df


def df_add_tod(df, attr="timestamp", tod_column_name="tod", timezone_name=DEFAULT_TIMEZONE):
    if attr not in ["date_time", "timestamp", "seconds_in_day"]:
        raise NotImplementedError
    if attr == "timestamp":
        df[tod_column_name] = pd.to_datetime(df[attr], unit='s', utc=True).dt.tz_convert(tz=timezone_name)
        df[tod_column_name] = df[tod_column_name].dt.hour + df[tod_column_name].dt.minute / 60.0 + df[
            tod_column_name].dt.second / 3600
    elif attr == "date_time":
        df[tod_column_name] = df.apply(lambda row: date_time_to_tod(row[attr]), axis=1)
    else:
        df[tod_column_name] = df.apply(lambda row: seconds_in_day_to_tod(row[attr]), axis=1)
    return df


def df_add_date_time(df, attr="timestamp", timezone_name=DEFAULT_TIMEZONE, date_time_column_name="date_time",
                     date_time_format=DATE_TIME_FORMAT):
    if attr not in ["timestamp", "tod", "seconds_in_day"]:
        raise NotImplementedError
    if attr == "timestamp":
        df[date_time_column_name] = pd.to_datetime(df[attr], unit='s', utc=True).dt.tz_convert(tz=timezone_name)
        df[date_time_column_name] = df[date_time_column_name].dt.strftime(date_time_format)
    elif attr == "tod":
        df[date_time_column_name] = df.apply(lambda row: tod_to_date_time(row[attr],
                                                                          date_time_format=date_time_format), axis=1)
    else:
        df[date_time_column_name] = df.apply(lambda row:
                                             seconds_in_day_to_date_time(row[attr], date_time_format=date_time_format),
                                             axis=1)
    return df


def df_add_seconds_in_day(df, attr="timestamp", timezone_name=DEFAULT_TIMEZONE,
                          seconds_in_day_column_name="seconds_in_day"):
    if attr not in ["timestamp", "date_time", "tod"]:
        raise NotImplementedError
    if attr == "timestamp":
        df[seconds_in_day_column_name] = df.apply(
            lambda row: get_seconds_in_day_from_timestamp(row[attr], timezone_name=timezone_name), axis=1)
    elif attr == "date_time":
        df[seconds_in_day_column_name] = df.apply(lambda row: date_time_to_seconds_in_day(row[attr]), axis=1)
    else:
        df[seconds_in_day_column_name] = df.apply(lambda row: tod_to_seconds_in_day(row[attr]), axis=1)
    return df


def timestamp_to_date_time_and_tod(timestamp, date_format=DATE_FORMAT, date_time_format=DATE_TIME_FORMAT,
                                   minute_interval=None, timezone_name=DEFAULT_TIMEZONE):
    ts = pd.Timestamp(timestamp, tz=timezone_name, unit='s')
    date = ts.strftime(date_format)
    if minute_interval is None:
        date_time = ts.strftime(date_time_format)
        tod = date_time_to_tod(date_time)
    else:
        new_minute = int(ts.minute / minute_interval) * minute_interval
        timestamp = timestamp - 60 * (ts.minute - new_minute)
        ts = pd.Timestamp(timestamp, tz=timezone_name, unit='s')
        date_time = ts.strftime(date_time_format)
        tod = date_time_to_tod(date_time)
    return date, date_time, tod


def tod_to_date_time(tod, date_time_format=DATE_TIME_FORMAT):
    """

    :param tod:
    :param date_time_format:
    :return:
    """
    if tod > 23.999 or tod < 0:
        print(f"tod {tod} not in [0, 23.999]")
        return None
    hour = int(tod)
    minute = int(np.round(60 * (tod - hour)))
    second = int(3600 * (tod - hour - minute / 60))
    if second < 0:
        minute -= 1
        second = int(3600 * (tod - hour - minute / 60))
    time_string = f"1970-01-01 {hour}:{minute}:{second}"
    ts = pd.Timestamp(time_string)
    return ts.strftime(date_time_format)


def get_seconds_in_day_from_timestamp(timestamp, timezone_name=DEFAULT_TIMEZONE):
    _, date_time, _ = timestamp_to_date_time_and_tod(timestamp, timezone_name=timezone_name)
    return date_time_to_seconds_in_day(date_time)


# def date_time_to_tod(date_time):
#     ts = pd.Timestamp("1970-01-01 " + date_time)
#     tod = ts.hour + ts.minute / 60.0 + ts.second / 3600.0
#     return tod

def date_time_to_tod(date_time):
    split_info = [int(val) for val in date_time.split(':')]
    tod = split_info[0] + split_info[1] / 60.0
    if len(split_info) == 3:
        tod += split_info[2] / 3600.0
    return tod


def tod_to_seconds_in_day(tod):
    return tod * 3600.0


def seconds_in_day_to_tod(seconds_in_day):
    return seconds_in_day / 3600.0


def date_time_to_seconds_in_day(date_time):
    return get_seconds_between_date_time("00:00", date_time)


def seconds_in_day_to_date_time(seconds_in_day, date_time_format=DATE_TIME_FORMAT):
    hour = int(seconds_in_day / 3600.0)
    minute = int((seconds_in_day - hour * 3600) / 60)
    second = int(seconds_in_day - hour * 3600 - minute * 60)
    time_string = f"1970-01-01 {hour}:{minute}:{second}"
    ts = pd.Timestamp(time_string)
    return ts.strftime(date_time_format)


def get_timestamp_from_date_tod(date, tod, timezone_name=DEFAULT_TIMEZONE):
    """
    get the timestamp given date and tod

    :param date:
    :param tod:
    :param timezone_name:
    :return:
    """
    if tod > 23.999 or tod < 0:
        print(f"tod {tod} not in [0, 23.999]")
        return None
    date_time = tod_to_date_time(tod)
    ts = pd.Timestamp(f"{date} {date_time}", tz=timezone_name)
    timestamp = ts.value // 10 ** 9
    return timestamp


def get_floor_timestamp(timestamp, floor_minute: int = None,
                        timezone_name=DEFAULT_TIMEZONE):
    """
    get the floor timestamp given certain timestamp

    :param timestamp:
    :param floor_minute:
    :param timezone_name:
    :return:
    """
    ts = pd.Timestamp(timestamp, unit="s", tz=timezone_name)
    new_minute = int(ts.minute / floor_minute) * floor_minute
    timestamp = timestamp - (ts.minute - new_minute) * 60
    return timestamp


def pandas_timestamp_to_string(ts, fmt=f"{DATE_FORMAT} {DATE_TIME_FORMAT}"):
    return ts.strftime(fmt)


def numpy_datetime64_to_string(ts, fmt=f"{DATE_FORMAT} {DATE_TIME_FORMAT}"):
    ts = pd.Timestamp(str(ts))
    return ts.strftime(fmt)


def string_to_pandas_timestamp(ts_string, timezone_name=DEFAULT_TIMEZONE):
    return pd.Timestamp(ts_string, tz=timezone_name)


def string_to_numpy_datetime64(ts_string):
    return np.datetime64(ts_string)


def get_seconds_between_tods(tod_1, tod_2):
    if tod_1 > 23.999 or tod_1 < 0:
        print(f"tod_1 {tod_1} not in [0, 23.999]")
        return None
    if tod_2 > 23.999 or tod_2 < 0:
        print(f"tod_2 {tod_2} not in [0, 23.999]")
        return None
    return (tod_2 - tod_1) * 3600


def get_seconds_between_date_time(date_time_1, date_time_2):
    tod_1 = date_time_to_tod(date_time_1)
    tod_2 = date_time_to_tod(date_time_2)
    return get_seconds_between_tods(tod_1, tod_2)


def get_date_range(start_date, end_date, date_interval=1, date_format=DATE_FORMAT):
    date_list = pd.date_range(start=start_date, end=end_date, freq=f"{date_interval}D")
    date_list = [ts.strftime(date_format) for ts in date_list]
    return date_list


def get_date_time_range(start_date_time, end_date_time, minute_interval=1, date_time_format=DATE_TIME_FORMAT):
    date_time_list = pd.date_range(start_date_time, end_date_time, freq=f"{minute_interval}min")
    date_time_list = [ts.strftime(date_time_format) for ts in date_time_list]
    return date_time_list


def add_tod_from_date_time(df, attr='date_time'):
    date_time_list = df[attr].tolist()
    tod_list = [float(val.split(":")[0]) + float(val.split(":")[1]) / 60 for val in date_time_list]
    df["tod"] = tod_list
    return df


def get_date_name(date_list):
    if len(date_list) == 1:
        return date_list[0]
    elif len(date_list) > 1:
        return date_list[0] + "_" + date_list[-1]


def get_date_time_list(resolution=20):
    """
    give resolution (min), output the full list of the time

    :param resolution: unit, minute should be divided by 60
    :return: ["00:00", "00:20", ..., "24:00"]
    """
    hourly_cuts = int(60 / resolution)
    total_nums = hourly_cuts * 24
    time_list = []
    for idx in range(total_nums):
        first_num = int(idx / hourly_cuts)
        first_string = str(first_num).zfill(2)
        second_num = int(idx % hourly_cuts) * resolution
        second_string = str(second_num).zfill(2)
        overall_time = f'{first_string}:{second_string}'
        time_list.append(overall_time)
    time_list += ['24:00']
    return time_list


def get_data_list_given_time_list(agg_df, channel_name, date_time_list, fillnan=0):
    """

    :param agg_df: aggregated df, with column ['date_time', channel_name]
    :param channel_name:
    :param date_time_list: ['00:00', '00:20', ...]
    :param fillnan:
    :return:
    """
    selected_time_list = date_time_list[:-1]

    channel_data_dict = {}
    time_list = agg_df['start_time'].tolist()
    channel_data_list = agg_df[channel_name].tolist()
    for (date_time, trajs_num) in zip(time_list, channel_data_list):
        channel_data_dict[date_time] = trajs_num

    new_channel_data_list = []
    for date_time in selected_time_list:
        if date_time in channel_data_dict.keys():
            new_channel_data_list.append(channel_data_dict[date_time])
        else:
            new_channel_data_list.append(fillnan)
    return new_channel_data_list


if __name__ == "__main__":
    dt1 = "10:03"
    dt2 = "21:02:59"
    tod1 = date_time_to_tod(dt1)
    tod2 = date_time_to_tod(dt2)

    print(tod1, tod_to_date_time(tod1))
    print(tod2, tod_to_date_time(tod2))
