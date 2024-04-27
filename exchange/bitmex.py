# coding=utf-8
import json
import logging
import time

import ccxt
import pandas as pd

import constants.constant as const
import db.db_sql as db
import response.error_code as code
import utils.time_util as time_util
from enums.used import Side, RunningStatus
from event.event_engine import Event, SymbolInfo, EventEngine
from exception.exception import QuantException
from model.params import OrderCreateParams
from parse.config import config
from push.base_exchange import BaseExchange
from realtime.bitmex_realtime import BitMexRealTime
from trade.base_trade import BaseTrade
from utils.base_utils import decimal_fmt


class BitMex(BaseExchange, BaseTrade):
    """
    BitMex 操作类
    """

    def __init__(self, exchange_name):
        # 初始化时间处理引擎
        self.strategy = None
        # ccxt 客户端
        self.ccxt_bitmex = ccxt.bitmex()
        self.ccxt_bitmex.load_markets()
        self.exchange_name = exchange_name
        # bitmex 客户端
        # self.bitmex_client = bitmex.bitmex(test=const.API_CONFIG[self.exchange_name][const.API_ENV]['test'],
        #                                    api_key=const.API_CONFIG[self.exchange_name][const.API_ENV]['apiKey'],
        #                                    api_secret=const.API_CONFIG[self.exchange_name][const.API_ENV]['secret'])

        # 币种信息
        self.running_id = None
        self.symbols = []
        self.exchange_symbols = config.get_exchange_symbols(self.exchange_name)
        print(self.exchange_symbols)
        self.max_limit = 500
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
    def start(self):
        if self.exchange_symbols is None:
            raise QuantException(code.FAIL, "请先设置启动的币种")

        super().start()
        # # 启动实时程序
        # BitMexRealTime().start()
        #
        # # 记录启动数据
        # self.running_id = db.insert_start(self.exchange_name, self.exchange_symbols)
        # return self.running_id

    # override
    def stop_after(self):
        super().stop_after()
        db.update_quant_running_status(self.running_id, RunningStatus.Stop.value)

    # override
    def init(self):
        pass
        # 全局引擎注册触发事件
        # EventEngine().register(self.exchange_name + '_quotation', self.event_handler)

        # # 初始化币种杠杆倍数
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

    # override
    def fetch_quotation(self):
        if len(self.exchange_symbols) == 0:
            return None

        frame_datas = []
        super().fetch_quotation()

        # 多币种同时获取数据
        for symbol_info in self.exchange_symbols:
            frame_dict = dict()

            now_time = int(time.time()) * 1000
            since_time = now_time - self.max_limit * 60 * 1000
            # 格式 时间  开  高  低  收  量
            ohlcv_data = self.ccxt_bitmex.fetch_ohlcv(symbol=symbol_info.symbol_pair_ccxt,
                                                      timeframe='5m',
                                                      since=since_time,
                                                      limit=self.max_limit)

            df = pd.DataFrame(ohlcv_data)
            df = df.rename(columns=const.DATA_COLUMNS)
            # 时间转换成北京时间
            df[const.TIME] = pd.to_datetime(df[const.TIME], unit='ms') + pd.Timedelta(hours=8)
            # 设置index
            df = df.set_index(const.TIME, drop=False)

            since_time = now_time - self.max_limit * 60 * 60 * 1000
            ohlcv_data_1h = self.ccxt_bitmex.fetch_ohlcv(symbol=symbol_info.symbol_pair_ccxt,
                                                         timeframe='1h',
                                                         since=since_time,
                                                         limit=self.max_limit)

            df_1h = pd.DataFrame(ohlcv_data_1h)
            df_1h = df_1h.rename(columns=const.DATA_COLUMNS)
            # 时间转换成北京时间
            df_1h[const.TIME] = pd.to_datetime(df_1h[const.TIME], unit='ms') + pd.Timedelta(hours=8)
            # 设置index
            df_1h = df_1h.set_index(const.TIME, drop=False)
            frame_dict['data_1h'] = df_1h

            frame_dict['data'] = self.__parse(df)
            frame_dict['symbol_info'] = symbol_info
            frame_dict['exchange_name'] = self.exchange_name
            frame_datas.append(frame_dict)
        return frame_datas

    # 数据转换成15分钟
    def __parse(self, frame_data):
        frame_data[const.TIME] = pd.to_datetime(frame_data[const.TIME])

        self.bars_15m = frame_data.resample('15min', on=const.TIME).agg({
            const.OPEN: 'first',
            const.HIGH: 'max',
            const.LOW: 'min',
            const.CLOSE: 'last',
            const.VOLUME: 'sum'
        })
        return self.bars_15m

    def fetch_order(self, symbol_info: SymbolInfo):
        super().fetch_order(symbol_info)

    def fetch_balance(self, symbol_info: SymbolInfo):
        balance = dict()
        wallet = self.bitmex_client.User.User_getWallet().result()
        balance['amount'] = wallet[0]['amount']
        balance['deposited'] = wallet[0]['deposited']
        balance['currency'] = wallet[0]['currency']
        balance['account'] = wallet[0]['account']
        return balance

    # override
    def create_order(self, params: OrderCreateParams, symbol_info: SymbolInfo):
        try:
            if params.price:
                print("实际开仓价格：%s" % decimal_fmt(params.price, 0))

                order_resp = self.bitmex_client.Order.Order_new(
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


