from event.event_engine import SymbolInfo
from model.params import OrderCreateParams
from trade.base_trade import BaseTrade


class BitMexTradeAPI(BaseTrade):
    """
    BitMex私人交易API接口实现类
    """
    def __init__(self):
        self.__realtime_engine = None
        pass

    def cancel_all_buy_orders(self, symbol_info: SymbolInfo):
        super().cancel_all_buy_orders(symbol_info)

    def fetch_balance(self, symbol_info: SymbolInfo):
        super().fetch_balance(symbol_info)

    def create_order(self, params: OrderCreateParams, symbol_info: SymbolInfo):
        super().create_order(params, symbol_info)

    def get_stock(self, symbol_info: SymbolInfo):
        super().get_stock(symbol_info)
