from enums.used import PositionType
from event.event_engine import SymbolInfo
from model.params import OrderCreateParams, Wallet, Position, OrderResp
from utils import time_util


class BaseTrade:

    def __init__(self):
        self.trade_cache = dict()
        self.before_price = None
        # 被动止损价格存储
        self.lose_price_cache = dict()
        # 被动止损胜率存储
        self.win_rate_cache = dict()
        self.latest_finish_period = None
        pass

    def set_last_trade_time(self, user_id=None, symbol_info: SymbolInfo = None):
        trade_key = '%s_%s' % (user_id, symbol_info.symbol_pair)
        self.trade_cache[trade_key] = time_util.now_timestamp_sec()

    def last_trade_interval(self, user_id=None, symbol_info: SymbolInfo = None):
        trade_key = '%s_%s' % (user_id, symbol_info.symbol_pair)
        if trade_key in self.trade_cache:
            return time_util.period(self.trade_cache[trade_key])

        return None

    def set_last_finish_period(self, period_time=None):
        self.latest_finish_period = period_time

    def get_last_finish_period(self):
        return self.latest_finish_period

    def cancel_all_buy_orders(self, symbol_info: SymbolInfo):
        # 取消所有委托
        return None

    def get_wallet(self, symbol_info: SymbolInfo) -> Wallet:
        # 获取账户余额
        return None

    def create_order(self, params: OrderCreateParams, symbol_info: SymbolInfo, leverage=None) -> OrderResp:
        # 创建订单
        return None

    def close_position(self, symbol_info: SymbolInfo, position_type=None):
        # 平仓
        return None

    def get_position(self, symbol_info: SymbolInfo) -> [Position]:
        # 获取仓位
        return None

    def set_leverage(self, symbol_info: SymbolInfo = None, leverage=None, position_type: PositionType = None):
        # 获取仓位
        return None

    def sync_remote_ledger(self, symbol_info: SymbolInfo, env=None):
        return None

    def set_before_price(self, price=None):
        self.before_price = price

    def get_before_price(self):
        return self.before_price

    def set_lose_price(self, user_id=None, symbol_info: SymbolInfo = None, price=None, direction=None):
        trade_key = '%s_%s_%s' % (user_id, symbol_info.symbol_pair, direction)
        self.lose_price_cache[trade_key] = price

    def get_lose_price(self, user_id=None, symbol_info: SymbolInfo = None, direction=None):
        trade_key = '%s_%s_%s' % (user_id, symbol_info.symbol_pair, direction)
        if trade_key in self.lose_price_cache:
            return self.lose_price_cache[trade_key]

        return None

    def set_win_rate(self, user_id=None, symbol_info: SymbolInfo = None, direction=None, rate=None):
        trade_key = '%s_%s_%s' % (user_id, symbol_info.symbol_pair, direction)
        self.win_rate_cache[trade_key] = rate

    def get_win_rate(self, user_id=None, symbol_info: SymbolInfo = None, direction=None):
        trade_key = '%s_%s_%s' % (user_id, symbol_info.symbol_pair, direction)
        if trade_key in self.win_rate_cache:
            return self.win_rate_cache[trade_key]

        return None
