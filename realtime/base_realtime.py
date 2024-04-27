from event.event_engine import SymbolInfo
from model.params import Position, Wallet


class BaseRealTime(object):

    def __init__(self):
        pass

    def get_position(self, symbol_info: SymbolInfo) -> Position:
        return None

    def get_wallet(self, symbol_info: SymbolInfo) -> Wallet:
        return None
