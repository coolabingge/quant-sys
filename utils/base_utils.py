import pandas as pd

import constants.constant as const


def decimal_fmt(val=None, pos=0):
    fmt = format(float(val), ('.%df' % pos))
    return float(fmt)


def handle_frame_data(frame_data=None):
    source_frame = pd.DataFrame(frame_data)
    # 添加列
    source_frame = source_frame.rename(columns=const.DATA_COLUMNS)
    # 时间转换成北京时间
    source_frame[const.TIME] = pd.to_datetime(source_frame[const.TIME], unit='ms') + pd.Timedelta(hours=8)
    # 设置index
    source_frame = source_frame.set_index(const.TIME, drop=False)
    return source_frame


def period_frame(frame_data=None, period=5):
    frame_data = handle_frame_data(frame_data)

    bars_period = frame_data.resample('%sT' % int(period), on=const.TIME).agg({
        const.OPEN: 'first',
        const.HIGH: 'max',
        const.LOW: 'min',
        const.CLOSE: 'last',
        const.VOLUME: 'sum'
    })

    bars_period = bars_period.dropna(axis=0, how='any')
    return bars_period

