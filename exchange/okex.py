# coding=utf-8
import json
import logging
import time

import ccxt
import numpy
from loguru import logger

import constants.constant as const
import db.db_sql as db
import response.error_code as code
from enums.used import Side, RunningStatus
from event.event_engine import SymbolInfo
from exception.exception import QuantException
from model.params import OrderCreateParams
from parse.config import config
from push.base_exchange import BaseExchange
from realtime.bitmex_realtime import BitMexRealTime
from trade.base_trade import BaseTrade
from utils import time_util
from utils.base_utils import decimal_fmt
from utils.cache_util import CacheUtil


class Okex(BaseExchange, BaseTrade):
    """
    Okex 操作类
    """

    def __init__(self, exchange_name):
        self.exchange_name = exchange_name
        # 初始化时间处理引擎
        self.strategy = None
        # okex 客户端
        self.ccxt_okex = ccxt.okex()
        self.ccxt_okex.proxies = const.PROXIES if const.USE_PROXY else None
        self.ccxt_okex.load_markets()

        # 币种信息
        self.running_id = None
        self.symbols = []
        self.exchange_symbols = config.get_exchange_symbols(self.exchange_name)

        # 一次获取1440个line点
        self.max_limit = 200
        self.trade_cache = dict()
        super().__init__(exchange_name)

    def set_symbols(self, symbols=[]):
        self.symbols = symbols
        if len(symbols) == 0:
            self.exchange_symbols = []

        execute_symbols = []
        for __index in range(len(self.exchange_symbols)):
            if self.exchange_symbols[__index].symbol in self.symbols:
                execute_symbols.append(self.exchange_symbols[__index])

        self.exchange_symbols = execute_symbols
        return self

    # override
    def name(self):
        return self.exchange_name

    # override
    def start(self, task_id=None):
        if self.exchange_symbols is None:
            raise QuantException(code.FAIL, "请先设置启动的币种")

        # 修正K线数据
        self.handle_history_line()
        # 加载历史K线数据进入缓存
        self.load_data_cache()
        super().start()

    # 加载历史K线数据进入缓存
    def load_data_cache(self):
        # 从数据库获取最近三天的K线数据进入内存
        now_time = int(time.time())
        start_time_ts = now_time - 3 * 24 * 3600
        for symbol_info in self.exchange_symbols:
            history_line = db.get_history_line(self.exchange_name, symbol_info.symbol_pair_ccxt, time_util.parse(start_time_ts))
            logger.info("cache history length: %s" % (len(history_line)))
            candle_dict = dict()
            for data in history_line:
                candle_ts = time_util.parse_ts(data['open_time'])
                candle = numpy.array([candle_ts, float(data['line_open']), float(data['high']), float(data['low']), float(data['line_close']), float(data['volume'])])
                candle_dict[candle_ts] = candle

            CacheUtil().set_line(self.exchange_name, symbol_info.symbol_pair_ccxt, candle_dict)

    # override
    def stop_after(self):
        super().stop_after()
        db.update_quant_running_status(self.running_id, RunningStatus.Stop.value)

    # 处理历史K线数据
    def handle_history_line(self):
        for symbol_info in self.exchange_symbols:
            max_time_dict = db.max_line_time(self.exchange_name, symbol_info.symbol_pair_ccxt)
            logger.info("max_time_dict: %s" % max_time_dict)
            db_max = None
            if max_time_dict['max_uxtime']:
                # 加上没有数据的当前一分钟
                db_max = max_time_dict['max_uxtime'] * 1000

            max_time_dict = db_max - 200 * 60 * 1000 or self.default_since_time()
            logger.info("平台：%s，币对：%s，最后K线时间：%s" % (self.exchange_name, symbol_info.symbol_pair_ccxt, time_util.parse(max_time_dict/1000)))

            now_time = int(time.time()) * 1000
            time_minus = (now_time - max_time_dict)//1000
            logger.info("相差分钟数: %d" % (time_minus//60))
            time_minus_count = (time_minus // 60) // 200
            logger.info("待补数据: %s * 200" % int(time_minus_count))
            for i in range(int(time_minus_count)):
                k_data = self.fetch_line(self.exchange_name, symbol_info.symbol_pair_ccxt, max_time_dict)
                logger.info("开始补数据, 条数：%s，时间：%s，unix：%d" % (len(k_data), time_util.parse(max_time_dict/1000), max_time_dict))
                db.insert_line(self.exchange_name, symbol_info.symbol_pair_ccxt, k_data)
                # 加上200分钟
                max_time_dict += 200 * 60 * 1000
                time.sleep(0.2)

    def default_since_time(self):
        now_time = int(time.time()) * 1000
        # 默认拉取前90天的数据持久化
        return now_time - 4 * 24 * 60 * 60 * 1000

    # override
    def init(self):
        pass
        # 全局引擎注册触发事件
        # 初始化币种杠杆倍数
        # for symbol_info in self.exchange_symbols:
        #     multiply = config.get(self.exchange_name, symbol_info.symbol, 'multiply')
        #     self.bitmex_client.Position.Position_updateLeverage(
        #         symbol=symbol_info.symbol_pair,
        #         leverage=multiply).result()

        # self.get_stock(self.exchange_symbols[0])
        # empty_stock_params = OrderCreateParams(
        #     side=Side.Buy,
        #     order_type=OrderType.Market,
        #     order_qty=20,
        # )
        # info_sym = SymbolInfo()
        # info_sym.symbol_pair = 'XBTUSD'
        # self.create_order(empty_stock_params, info_sym)

    def parse_position(self, position_result):
        position_data = dict()
        for pos in position_result[0]:
            position_data[pos['symbol']] = pos['leverage']

        return position_data

    # 获取1分钟K线数据
    def fetch_line(self, market=None, symbol=None, since_time=None):
        ohlcv_data = self.ccxt_okex.fetch_ohlcv(symbol=symbol,
                                                timeframe='1m',
                                                since=since_time,
                                                limit=300,
                                                params={"type":'Candles'})
        if not ohlcv_data:
            time.sleep(0.5)
            ohlcv_data = self.ccxt_okex.fetch_ohlcv(symbol=symbol,
                                                timeframe='1m',
                                                since=since_time,
                                                limit=300,
                                                params={"type":'HistoryCandles'})

        return ohlcv_data

    # override
    def fetch_quotation(self):
        if len(self.exchange_symbols) == 0:
            return None

        frame_datas = []

        # 多币种同时获取数据
        for symbol_info in self.exchange_symbols:
            frame_dict = dict()

            now_time = int(time.time()) * 1000
            # K线越多越准
            since_time = now_time - 200 * 60 * 1000
            # 格式 时间  开  高  低  收  量
            ohlcv_data = self.ccxt_okex.fetch_ohlcv(symbol=symbol_info.symbol_pair_ccxt,
                                                    timeframe='1m',
                                                    since=since_time,
                                                    limit=self.max_limit)

            # 缓存数据
            CacheUtil().set_line(self.exchange_name, symbol_info.symbol_pair_ccxt, ohlcv_data)
            # 合并之前历史数据
            line_data = CacheUtil().get_line(self.exchange_name, symbol_info.symbol_pair_ccxt)

            line_arr = []
            for open_time in line_data:
                line_arr.append(line_data[open_time])
            #
            # if symbol_info.symbol_pair_ccxt == 'LTC-USDT-SWAP':
            #     dfx = pd.DataFrame(line_arr)
            #     dfx = dfx.rename(columns=const.DATA_COLUMNS)
            #     # 时间转换成北京时间
            #     dfx[const.TIME] = pd.to_datetime(dfx[const.TIME], unit='ms') + pd.Timedelta(hours=8)
            #     # 设置index
            #     dfx = dfx.set_index(const.TIME, drop=False)
            #     after_data = base_utils.period_frame(line_arr, 5)
            #     after_data = after_data.dropna(axis=0, how='any')
            #     print(after_data.close.tolist())
            #     print(QuantCommon('OKEX').result(after_data))

            frame_dict['data'] = line_arr
            frame_dict['symbol_info'] = symbol_info
            frame_dict['exchange_name'] = self.exchange_name
            frame_datas.append(frame_dict)

        return frame_datas

    def fetch_order(self, symbol_info: SymbolInfo):
        super().fetch_order(symbol_info)

    # override
    def create_order(self, params: OrderCreateParams, symbol_info: SymbolInfo):
        try:
            if params.price:
                print("实际开仓价格：%s" % decimal_fmt(params.price, 0))

                order_resp = self.bitmex_client.Order.Order_new(
                    client_oid=params.client_oid,
                    symbol=symbol_info.symbol_pair,
                    side=params.side,
                    ordType=params.order_type,
                    price=decimal_fmt(params.price, 0),
                    orderQty=params.order_qty).result()
                return order_resp
            else:
                print("市价开单..")
                order_resp = self.bitmex_client.Order.Order_new(
                    symbol=symbol_info.symbol_pair,
                    side=params.side,
                    ordType=params.order_type,
                    orderQty=params.order_qty).result()
                return order_resp
        except Exception as e:
            logging.info('创建订单失败, 错误: %s', e.swagger_result['error']['message'])
            raise e

        return None

    def fetch_open_buy_orders(self, symbol_info: SymbolInfo):
        orders = self.bitmex_client.Order.Order_getOrders(
            symbol=symbol_info.symbol_pair,
            filter=json.dumps({"open": True, "side": Side.Buy.value})).result()
        return orders

    """
    获取个人仓位数据
    """

    def get_stock(self, symbol_info: SymbolInfo):
        __columns = ["currentQty", "openOrderBuyQty", "openOrderSellQty", "openOrderBuyCost", "openOrderSellCost",
                     "avgCostPrice", "unrealisedPnlPcnt", "symbol", "markPrice", "liquidationPrice"]

        orders = self.bitmex_client.Position.Position_get(
            filter=json.dumps({"symbol": symbol_info.symbol_pair}),
            columns=json.dumps(__columns)).result()
        my_stock = []
        for pos in orders[0]:
            __stock = dict()
            # 开仓价
            __stock['avgCostPrice'] = pos['avgCostPrice']
            # 合约量
            __stock['currentQty'] = pos['currentQty']
            __stock['openOrderBuyQty'] = pos['openOrderBuyQty']
            __stock['openOrderSellQty'] = pos['openOrderSellQty']
            __stock['openOrderBuyCost'] = pos['openOrderBuyCost']
            __stock['openOrderSellCost'] = pos['openOrderSellCost']
            # 币种
            __stock['symbol'] = pos['symbol']
            # 标记价格
            __stock['markPrice'] = pos['markPrice']
            # 强平价格
            __stock['liquidationPrice'] = pos['liquidationPrice']
            # 回报率
            __stock['unrealisedPnlPcnt'] = pos['unrealisedPnlPcnt']

            my_stock.append(__stock)

        return my_stock

    def cancel_all_buy_orders(self, symbol_info: SymbolInfo):

        self.bitmex_client.Order.Order_cancelAll(
            symbol=symbol_info.symbol_pair).result()

    def realtime(self):
        super().realtime()
        # 单例
        return BitMexRealTime()


