# coding=utf-8
import json

import db.db_sql as db
import response.error_code as code
from event.event_engine import SymbolInfo
from exception.exception import QuantException
from model.params import QuantUserExchange, QuantExchange


class Config(object):
    conf = {}

    def __init__(self):
        self.conf = dict()
        self.user_conf = dict()
        self.market_conf = dict()
        self.strategy_market = []

        self.__init_config()

    def info(self):
        return self.conf

    def get(self, exchange, symbol, key):
        if exchange not in self.conf:
            raise QuantException(code.FAIL, "暂无此交易所配置项,交易所代号：" + exchange)

        if symbol not in self.conf[exchange]:
            raise QuantException(code.FAIL, exchange + "交易所下暂无此币种配置，币种代号：：" + symbol)

        if key not in self.conf[exchange][symbol]:
            return self.conf['GLOBAL']['GLOBAL'][key]
        else:
            return self.conf[exchange][symbol][key]

    def get_user(self, user_id=None, market_name=None, env=None) -> QuantUserExchange:
        if user_id not in self.user_conf:
            raise QuantException(code.FAIL, "用户配置不存在, id: %s" % (user_id))
        if market_name not in self.user_conf[user_id]:
            raise QuantException(code.FAIL, "用户交易所配置不存在, id: %s, market_name: %s" % (user_id, market_name))
        if env not in self.user_conf[user_id][market_name]:
            raise QuantException(code.FAIL,
                                 "用户交易所环境配置不存在, id: %s, market_name: %s, env: %s" % (user_id, market_name, env))

        return self.user_conf[user_id][market_name][env]

    def get_market(self, market_symbol) -> QuantExchange:
        return self.market_conf[market_symbol]

    def get_exchange_symbols(self, exchange):
        if exchange not in self.conf:
            raise QuantException(code.FAIL, "暂无此交易所配置项,交易所代号：" + exchange)

        exchange_symbols = []
        for key in self.conf[exchange]:
            __symbol_info = SymbolInfo()
            __symbol_info.symbol = key
            __symbol_info.currency = self.conf[exchange][key]['currency']
            __symbol_info.symbol_pair = self.conf[exchange][key]['symbol_pair']
            __symbol_info.symbol_pair_ccxt = self.conf[exchange][key]['symbol_pair_ccxt']

            exchange_symbols.append(__symbol_info)

        return exchange_symbols

    def reload(self):
        self.__init_config()

    def get_strategy_market(self):
        return self.strategy_market

    def __init_config(self):
        # 策略配置处理
        strategy_confs, count = db.get_quant_config()

        for strategy_conf in strategy_confs:
            if strategy_conf['exchange'] not in self.conf:
                self.conf[strategy_conf['exchange']] = dict()

            self.conf[strategy_conf['exchange']][strategy_conf['symbol']] = strategy_conf

            col_config_dict = json.loads(strategy_conf['config'])
            for key in col_config_dict:
                self.conf[strategy_conf['exchange']][strategy_conf['symbol']][key] = col_config_dict[key]
            self.conf[strategy_conf['exchange']][strategy_conf['symbol']].pop('config')

        # 用户配置处理
        user_db_conf, user_count = db.get_quant_user_exchange()
        for s_user in user_db_conf:
            if s_user['user_id'] not in self.user_conf:
                self.user_conf[s_user['user_id']] = dict()

            if s_user['exchange'] not in self.user_conf[s_user['user_id']]:
                self.user_conf[s_user['user_id']][s_user['exchange']] = dict()

            if s_user['env'] not in self.user_conf[s_user['user_id']][s_user['exchange']]:
                self.user_conf[s_user['user_id']][s_user['exchange']][s_user['env']] = dict()

            self.user_conf[s_user['user_id']][s_user['exchange']][s_user['env']] = QuantUserExchange(
                ue_id=s_user['id'],
                user_name=s_user['user_name'],
                user_id=s_user['user_id'],
                exchange=s_user['exchange'],
                api_key=s_user['api_key'],
                secret=s_user['secret'],
                passphrase=s_user['passphrase'],
                env=s_user['env']
            )

        # 交易所配置处理
        market_confs, count = db.get_quant_exchange()
        for market in market_confs:
            if market['exchange'] not in self.market_conf:
                self.market_conf[market['exchange']] = dict()

            self.market_conf[market['exchange']] = QuantExchange(
                exchange_name=market['exchange_name'],
                exchange=market['exchange'],
                instance_class=market['instance_class'],
                api_dist_http=market['api_dist_http'],
                api_dist_websocket=market['api_dist_websocket'],
                api_test_http=market['api_test_http'],
                api_test_websocket=market['api_test_websocket'],
            )

            if (market['exchange'] not in self.strategy_market) and (market['exchange'] in self.conf):
                self.strategy_market.append(self.market_conf[market['exchange']])


print('system config init...')
config = Config()
print('system config init success...')
