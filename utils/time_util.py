import datetime
import time


def now(pattern="%Y-%m-%d %H:%M:%S"):
    """
    当前格式化时间
    """
    return datetime.datetime.now().strftime(pattern)


def parse(ux_time=None, pattern="%Y-%m-%d %H:%M:%S"):
    if ux_time:
        time_tuple = time.localtime(ux_time)  # 把时间戳转换成时间元祖
        result = time.strftime(pattern, time_tuple)  # 把时间元祖转换成格式化好的时间
        return result
    else:
        return time.strptime(pattern)


def parse_ts(p_time=None, pattern="%Y-%m-%d %H:%M:%S"):
    """
    转换时间为时间戳，单位：ms
    :param p_time:
    :param pattern:
    :return:
    """
    time_array = time.strptime(p_time, pattern)
    return int(time.mktime(time_array)) * 1000


def now_timestamp_sec():
    """
    当前的秒级时间戳时间
    """
    return int(time.time())


def period(past_second_time):
    """
    与当前的时间差
    """
    return now_timestamp_sec() - past_second_time


def utc2string(utc_timestamp):
    utc_source_format = "%Y-%m-%dT%H:%M:%S.%fZ"
    utc_time = datetime.datetime.strptime(utc_timestamp, utc_source_format)
    after_time = "%Y-%m-%d %H:%M:%S"
    return (utc_time + datetime.timedelta(hours=8)).strftime(after_time)


print(parse_ts('2021-01-15 23:54:00'))
