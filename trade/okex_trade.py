from pprint import pprint

from loguru import logger

import db.db_sql as db
from enums.used import OrderType, PositionType, Env
from event.event_engine import SymbolInfo
from exception.exception import QuantException
from model.params import OrderCreateParams, QuantUserExchange, Position, Wallet, OrderResp
from trade.base_trade import BaseTrade
from utils.base_utils import decimal_fmt
from utils.okex_client import OkexClient
from utils.time_util import utc2string


class OkexTradeAPI(BaseTrade):
    """
    OKEX私人交易API接口实现类
    """

    """
        0：普通委托（order_type不填或填0都是普通委托）
        1：只做Maker（Post only）
        2：全部成交或立即取消（FOK）
        3：立即成交并取消剩余（IOC）
        4：市价委托
    """
    order_type = {
        OrderType.Limit.value: 0,
        OrderType.Market.value: 4
    }

    def __init__(self, user_id=None, api_trade_config: QuantUserExchange = None, env: Env = None, task_id=None, strategy=None):
        super().__init__()
        self.user_id = user_id
        self.task_id = task_id
        self.before_price = None
        self.env = env

        self.__realtime_engine = None
        self.strategy = strategy
        self.api_client = OkexClient(api_key=api_trade_config.api_key,
                                     api_seceret_key=api_trade_config.secret,
                                     passphrase=api_trade_config.passphrase,
                                     env=env)

    def cancel_all_buy_orders(self, symbol_info: SymbolInfo):
        super().cancel_all_buy_orders(symbol_info)
        # 获取所有未生效委托单列表
        ret = self.api_client.get_order_list(status=0, instrument_id=self.__env_symbol(symbol_info))
        algo_orders = []
        if ret and ret['order_info']:
            for algo in ret['order_info']:
                algo_orders.append(algo['order_id'])

        if len(algo_orders) > 0:
            self.api_client.revoke_orders(ids=algo_orders, instrument_id=self.__env_symbol(symbol_info))
            logger.info("撤下所有委托单: %s" % algo_orders)

        return algo_orders

    def create_order(self, params: OrderCreateParams, symbol_info: SymbolInfo, leverage=None) -> OrderResp:
        super().create_order(params, symbol_info)

        rate = 10
        # BTC 一张 = 100美元，其他 一张 = 10美元
        if symbol_info.symbol_pair == 'BTC-USDT-SWAP':
            rate = 100

        # 注意下单单位，这里qty是下单金额
        # size = decimal_fmt(params.order_qty * leverage / params.price, 2)
        size = decimal_fmt(params.order_qty / rate, 2)
        size = int(size)
        if size == 0:
            size = 1

        # size必须是证书，且最少为1
        logger.info("开单数量：%s, 开单模式：市价开单，币种：%s" % (size, symbol_info.symbol_pair))
        # type = 1:开多 2: 开空 3:平多 4：平空
        resp = self.api_client.take_order(instrument_id=self.__env_symbol(symbol_info),
                                          # 下单数量，买入或卖出合约的数量USDT计数
                                          size=size,
                                          otype=params.side.value,
                                          price=None,
                                          client_oid=params.client_oid,
                                          match_price=None,
                                          order_type=0 if (params.side.value == 'Limit') else 4)

        logger.info("create_order resp: %s" % resp)
        return OrderResp(order_id=resp['order_id'], success=(resp['error_code'] == 0))

    def get_wallet(self, symbol_info: SymbolInfo) -> Wallet:
        super().get_wallet(symbol_info)
        rst = self.api_client.get_coin_account(self.__env_symbol(symbol_info))
        print(rst)
        return Wallet(account=None,
                      amount=rst['info']['equity'],
                      currency=rst['info']['currency'],
                      used=rst['info']['margin'])

    def __env_symbol(self, symbol: SymbolInfo):
        if self.env == Env.Test:
            return 'MN%s' % symbol.symbol_pair

        return symbol.symbol_pair

    def get_settings(self, symbol_info: SymbolInfo):
        return self.api_client.get_settings(self.__env_symbol(symbol_info))

    def get_position(self, symbol_info: SymbolInfo) -> [Position]:
        rst = self.api_client.get_specific_position(self.__env_symbol(symbol_info))
        positions = []
        if rst and rst['holding']:
            for hold in rst['holding']:
                positions.append(Position(account=None,
                                          symbol=hold['instrument_id'],
                                          leverage=hold['leverage'],
                                          current_qty=hold['margin'],
                                          current_cost=None,
                                          buy_price=hold['avg_cost'],
                                          home_notional=None,
                                          # long 做多，short： 做空
                                          direction=hold['side']))

        return positions

    def set_leverage(self, symbol_info: SymbolInfo = None, leverage=None, position_type: PositionType = None):
        super().set_leverage(symbol_info, leverage, position_type)
        try:
            # 1: 逐仓-多,2:逐仓-空，3：全仓
            self.api_client.set_leverage(instrument_id=self.__env_symbol(symbol_info),
                                         leverage=leverage,
                                         # 1:逐仓-多仓
                                         # 2:逐仓-空仓
                                         # 3:全仓
                                         side=1 if position_type.value == 'long' else 2)
        except Exception as e:
            raise QuantException(message="设置杠杆倍数失败(%s)" % e)

    def close_position(self, symbol_info: SymbolInfo, position_type=None):
        ret = self.api_client.close_position(self.__env_symbol(symbol_info), position_type)
        logger.info("平仓结果：%s" % ret)

    def set_before_price(self, price=None):
        super().set_before_price(price)

    def get_before_price(self):
        return super().get_before_price()

    def sync_remote_trades(self, symbol_info: SymbolInfo):
        trades = self.api_client.get_order_list(instrument_id=self.__env_symbol(symbol_info), status=2)
        if trades and trades['order_info']:
            params = []
            for data in trades['order_info']:
                param = (self.task_id, symbol_info.symbol_pair,
                         data['client_oid'], data['size'], utc2string(data['timestamp']), data['filled_qty'],
                         data['fee'], data['order_id'], data['price'], data['price_avg'], data['type'],
                         data['contract_val'], data['order_type'], data['state'], data['trigger_price'],
                         data['leverage'])
                params.append(param)

            print(params)
            db.batch_insert_orders(params)

    def sync_remote_algo_orders(self, symbol_info:SymbolInfo):
        algo_orders = self.api_client.get_algo_orders(instrument_id=self.__env_symbol(symbol_info))
        pprint(algo_orders)

    def sync_remote_ledger(self, symbol_info: SymbolInfo, env=None):
        max_ledger_id = db.get_max_ledger_id(self.task_id)
        ledgers = self.api_client.get_ledger(instrument_id=self.__env_symbol(symbol_info), froms=max_ledger_id)
        if ledgers and len(ledgers) > 0:
            params = []
            for ledger in ledgers:
                if ledger['details'] and ledger['type'] == 'match' and ledger['details']['order_id']:
                    param = (self.task_id, symbol_info.symbol_pair,
                             ledger['balance'], ledger['currency'], ledger['instrument_id'], ledger['details']['order_id'],
                             ledger['fee'], ledger['ledger_id'], utc2string(ledger['timestamp']), ledger['type'],
                             ledger['amount'], self.strategy, env)
                    params.append(param)

            db.batch_insert_ledgers(params)
