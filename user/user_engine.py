import threading

from loguru import logger

import db.db_sql as db
from enums.used import Env, PositionType
from event.event_engine import Event, EventEngine, SymbolInfo
from exception.exception import QuantException
from model.params import QuantUserExchange
from parse.config import config
from strategy.macd_finish_strategy import MACDFinishStrategy
from trade.base_trade import BaseTrade
from trade.okex_trade import OkexTradeAPI
from utils import time_util
from utils.cache_util import CacheUtil, RUN_TASK_KEY


class UserRunEngine(object):
    """
    用户执行引擎，具体执行某个交易所下的某个用户的策略任务
    """
    def __init__(self, market, user_id, env: Env = Env.Dist, strategy=1, task_config=None, task_id=None, symbol=None, task_obj=None):
        self.__market = market
        self.__user_id = user_id
        self.__start = False
        self.__trade_api: BaseTrade = None
        self.__leverage_setting = None
        # 杠杆倍数，任务配置获取
        self.leverage = task_config['multiply']
        self.env = env
        self.strategy = strategy
        self.last_data_sync_time = None
        self.lock = threading.RLock()
        self.user_market_config: QuantUserExchange = None
        self.task_config = task_config
        self.task_id = task_id
        # 任务注册的币种
        self.symbol = symbol
        self.task_obj = task_obj

    def data(self, event: Event):
        if not self.__start:
            return

        try:
            self.__handle_leverage(event.symbol_info)
        except QuantException as e:
            logger.info("%s设置杠杆失败" % self.symbol)
            return
        try:
            # 判断执行哪个策略
            # if self.strategy == 1:
            #     FirstStrategy(cur_price, result, event, self.__trade_api, result_1h, self.__user_id,
            #                   self.leverage, self.env).execute()
            # elif self.strategy == 2:
            #     MACDStrategy(cur_price, result, event, self.__trade_api, result_1h, self.__user_id,
            #                  self.leverage, self.env).execute()
            if self.strategy == 3:
                MACDFinishStrategy(self.__trade_api, event, self.__user_id, self.task_config, self.env, self.task_id).execute()
            # elif self.strategy == 4:
            #     FirstFinishStrategy(cur_price, result, event, self.__trade_api, result_1h, self.__user_id,
            #                        self.leverage, self.env).execute()
            #
            # self.__trade_api.set_before_price(cur_price)
            # 同步服务器流水数据
            self.sync_data(event.symbol_info)
        except Exception as e:
            raise e

    def __handle_leverage(self, symbol_info: SymbolInfo = None):
        if not self.__leverage_setting:
            self.__leverage_setting = self.__trade_api.get_settings(symbol_info)
            # 设置此种交易对杠杆,做多，做空各配置的倍数
            if self.__leverage_setting['long_leverage'] != self.leverage:
                self.__trade_api.set_leverage(symbol_info, self.leverage, PositionType.More)

            if self.__leverage_setting['short_leverage'] != self.leverage:
                self.__trade_api.set_leverage(symbol_info, self.leverage, PositionType.Empty)

    def test(self):
        user_market_config = config.get_user(user_id=self.__user_id, market_name=self.__market, env=self.env.value)
        self.__trade_api = OkexTradeAPI(self.__user_id, user_market_config, env=self.env,
                                        task_id=self.task_id, strategy=self.strategy)
        symbol_info = SymbolInfo()
        symbol_info.symbol = 'BTC'
        symbol_info.symbol_pair = 'BTC-USDT-SWAP'
        self.__trade_api.sync_remote_ledger(symbol_info, self.env.value)
        # print(self.__trade_api.get_position(symbol_info))
        # print(self.__trade_api.set_leverage(symbol_info, 20, PositionType.More))
        # self.__trade_api.cancel_all_buy_orders(symbol_info)
        # self.__trade_api.close_position(symbol_info, PositionType.More)

        # self.__trade_api.set_lose_price(self.__user_id, symbol_info, 12345.1, 'long')
        # print(self.__trade_api.get_lose_price(self.__user_id, symbol_info, 'long'))
        # order_create_params = OrderCreateParams(
        #     side=Side.Open_More,
        #     order_type=OrderType.Limit,
        #     price=13000,
        #     order_qty=10,
        #     win_rate=0,
        #     status='open'
        # )
        #
        # self.__trade_api.create_order(order_create_params, symbol_info, leverage=50)

    def __ready(self):
        self.user_market_config = config.get_user(user_id=self.__user_id, market_name=self.__market, env=self.env.value)
        success = self._add_run_task()
        if not success:
            logger.warning("当前用户任务已经启动，无法重复执行")
            return

        # 注册数据
        event_name = self.__market + "_" + self.symbol + '_quotation'
        logger.info("User [%s] register [%s(%s)] Kline Data." % (self.__user_id, self.__market, self.symbol))
        EventEngine().register(event_name, self.data)
        self.__trade_api = OkexTradeAPI(user_id=self.__user_id, api_trade_config=self.user_market_config, env=self.env,
                                        task_id=self.task_id, strategy=self.strategy)

    def start(self):
        self.__ready()
        self.__start = True

    def stop(self):
        self._remove_run_task()
        self._remove_runtime_quota()
        self.__start = False
        EventEngine().unregister(self.__market + '_' + self.symbol + '_quotation', self.data)

    # def _add_runtime_quota(self, quota_data=None):
    #     if not self.task_id:
    #         return
    #
    #     all_quota = CacheUtil().get(REALTIME_QUOTA % (self.__market, self.symbol))
    #     all_quota = all_quota if all_quota else {}
    #     all_quota[self.task_id] = quota_data
    #     CacheUtil().set(REALTIME_QUOTA % (self.__market, self.symbol), all_quota)

    # def _remove_runtime_quota(self):
    #     if not self.task_id:
    #         return
    #
    #     all_quota = CacheUtil().get(REALTIME_QUOTA % (self.__market, self.symbol))
    #     all_quota = all_quota if all_quota else {}
    #     if self.task_id in all_quota:
    #         del all_quota[self.task_id]
    #         CacheUtil().set(REALTIME_QUOTA % (self.__market, self.symbol), all_quota)

    def _add_run_task(self):
        # 检查当前内存有无启动任务
        run_list = CacheUtil().get(RUN_TASK_KEY)
        run_list = run_list if run_list else {}
        if self.task_id not in run_list:
            run_list[self.task_id] = self.task_obj
            CacheUtil().set(RUN_TASK_KEY, run_list)
            return True
        else:
            return False

    def _remove_run_task(self):
        if not self.task_id:
            return

        # 从内存中移除
        run_list = CacheUtil().get(RUN_TASK_KEY)
        run_list = run_list if run_list else {}
        if self.task_id in run_list:
            del run_list[self.task_id]
            CacheUtil().set(RUN_TASK_KEY, run_list)
        db.disable_task(self.task_id)

    def sync_data(self, symbol_info: SymbolInfo):
        self.lock.acquire()
        try:
            if not self.last_data_sync_time:
                self.__trade_api.sync_remote_ledger(symbol_info, self.env.value)
                self.last_data_sync_time = time_util.now_timestamp_sec()

            if self.__start and self.last_data_sync_time and (time_util.period(self.last_data_sync_time) >= 5 * 60):
                self.__trade_api.sync_remote_ledger(symbol_info, self.env.value)
                self.last_data_sync_time = time_util.now_timestamp_sec()
        except Exception as e:
            logger.warning(e)
        finally:
            self.lock.release()

# MarketEngine().run()
# UserRunEngine('OKEX', 2, Env.Test).test()
# UserRunEngine('OKEX', 2).start()
