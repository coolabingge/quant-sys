import talib

import constants.constant as const


class QuantCommon:
    """
    量化常用算法类，共用类，根据K线可以获取所有交易所的均线指标算法
    """

    def __init__(self, market=None):
        self.market = market
        self.period_config = const.ALGORITHM_CONFIG[market] or const.ALGORITHM_CONFIG['DEFAULT']
        self.algorithm_result = dict()

    def result(self, bars_data):
        base_frame = bars_data
        self.algorithm_result = dict()

        self.__ma(base_frame)
        # self.__ema(bars_data)
        self.__macd(base_frame)
        self.__boll(base_frame)
        self.__bbi(base_frame)
        return self.algorithm_result

    """
    根据K线数据计算MA指标线
    """

    def __ma(self, bars_data):
        for period in self.period_config['MA']:
            self.algorithm_result['MA_' + str(period)] = self.__single_ma(bars_data, period)

    def __single_ma(self, bars_data, period):
        return bars_data[const.CLOSE].rolling(period).mean()

    """
    根据K线数据计算EMA指标线
    """

    def __ema(self, bars_data):
        ema_list = self.period_config['EMA']
        for period in ema_list:
            self.algorithm_result['EMA_' + str(period)] = talib.EMA(bars_data[const.CLOSE], period)

    """
    根据K线数据计算macd线
    """

    def __macd(self, bars_data):
        _short = self.period_config['MACD'][0]
        _long = self.period_config['MACD'][1]
        _move_avg = self.period_config['MACD'][2]

        _dif, _dea, _macd = talib.MACD(bars_data[const.CLOSE], fastperiod=_short, slowperiod=_long, signalperiod=_move_avg)
        self.algorithm_result['MACD_DIFF'] = _dif[-2:][-1]
        self.algorithm_result['MACD_DEA'] = _dea[-2:][-1]
        self.algorithm_result['MACD'] = _macd[-2:][-1]
        self.algorithm_result['MACD_BEFORE'] = _macd[-2:][-2]
        # print(self.algorithm_result['MACD_DIFF'], self.algorithm_result['MACD_DEA'], self.algorithm_result['MACD'])

    """
    根据K线数据计算布林线
    """

    def __boll(self, bars_data):
        boll_config = self.period_config['BOLL']
        boll_data = dict()
        boll_data['median'] = bars_data[const.CLOSE].rolling(boll_config[0], min_periods=1).mean()
        # ddof代表标准差自由度
        boll_data['std'] = bars_data[const.CLOSE].rolling(boll_config[0], min_periods=1).std(ddof=0)
        boll_data['upper'] = boll_data['median'] + boll_config[1] * boll_data['std']
        boll_data['lower'] = boll_data['median'] - boll_config[1] * boll_data['std']

        self.algorithm_result['BOLL_UPPER'] = boll_data['upper'][-2:][-1]
        self.algorithm_result['BOLL_LOWER'] = boll_data['lower'][-2:][-1]
        self.algorithm_result['BOLL_STD'] = boll_data['std'][-2:][-1]
        self.algorithm_result['BOLL_MEDIAN'] = boll_data['median'][-2:][-1]

    """
    根据K线数据计算BBI线
    """

    def __bbi(self, bars_data):
        # 4个周期的MA 均线
        # bbi_config = self.period_config['BBI']
        bbi_data = dict()
        # for period in bbi_config:
        #     if 'bbi' not in bbi_data:
        #         bbi_data['bbi'] = self.__single_ma(bars_data, period)
        #     else:
        #         bbi_data['bbi'] = bbi_data['bbi'] + self.__single_ma(bars_data, period)
        bbi_data['bbi'] = talib.MA(bars_data[const.CLOSE], timeperiod=3, matype=0) + \
                          talib.MA(bars_data[const.CLOSE], timeperiod=6, matype=0) + \
                          talib.MA(bars_data[const.CLOSE], timeperiod=12, matype=0) + \
                          talib.MA(bars_data[const.CLOSE], timeperiod=24, matype=0)

        bbi_data['bbi'] = bbi_data['bbi'] / 4
        self.algorithm_result['BBI'] = bbi_data['bbi'][-2:][-1]
