import json

from loguru import logger
from singleton_decorator import singleton

import db.db_sql as db
from daemon.linethread import LineThread
from enums.used import Env
from event.event_engine import EventEngine
from exchange.okex import Okex
from parse.config import config
from user.user_engine import UserRunEngine


@singleton
class MarketEngine(object):

    """
    交易所引擎
    目的：启动所有交易所，作为K线数据生产者
    启动时间：跟随系统启动而启动
    """
    def __init__(self):
        self.markets = []

        self.__ready()

    def run(self):
        # 启动事件引擎
        logger.info("[Data Engine] Starting...")
        EventEngine().start()

        LineThread().start()
        switch = {
            # 'BITMEX': BitMex('BITMEX'),
            'OKEX': Okex('OKEX')
        }

        self.markets = config.get_strategy_market()
        for market in self.markets:
            # symbols = config.get_exchange_symbols(market.exchange)
            switch[market.exchange].start()

        logger.info("[Data Engine] Start Success...")
        logger.info("[Data Engine] Start recover runnable task...")
        runnable_task = db.get_running_task()
        if runnable_task and len(runnable_task) > 0:
            for task_obj in runnable_task:
                logger.info('[Resume Task]: %s, config: %s' % (task_obj['id'], task_obj['config']))
                UserRunEngine(market=task_obj['exchange'],
                              user_id=task_obj['user_id'],
                              env=Env.Dist if task_obj['env'] == 'Dist' else Env.Test,
                              strategy=task_obj['strategy_no'],
                              task_config=json.loads(task_obj['config']),
                              task_id=task_obj['id'],
                              symbol=task_obj['symbol_pair'],
                              task_obj=task_obj).start()

    def __ready(self):
        market_infos, count = db.get_quant_exchange()
        for market in market_infos:
            self.markets.append(market['exchange'])
