import hashlib
import hmac
import json
import time
import urllib

import websocket
from singleton_decorator import singleton

from event.event_engine import SymbolInfo
from model.params import Position, Wallet, QuantUserExchange
from parse.config import config
from realtime.base_realtime import BaseRealTime
from wssocket.conn import Conn, Proxy


class BitMexRealTime(BaseRealTime):
    name = "BITMEX"

    def __init__(self):
        self.user_exchange: QuantUserExchange = None
        self.position = dict()
        self.wallet = dict()
        self.conn = None

    def start(self, user_exchange: QuantUserExchange = None):
        self.user_exchange = user_exchange
        market_config = config.get_market(user_exchange.exchange)
        self.conn = Conn(ws_url=market_config.api_dist_websocket,
                         proxy=Proxy("127.0.0.1", 61999),
                         on_message=self.__on_message,
                         on_error=self.__on_error,
                         on_close=self.__on_close,
                         on_open=self.__on_open,
                         header=self.__get_auth())

        self.conn.connect()

    def reconnect(self):
        self.position.clear()
        self.wallet.clear()
        self.start(self.user_exchange)

    def generate_nonce(self):
        return int(round(time.time() + 3600))

    def generate_signature(self, verb, url, nonce, data):
        parsed_url = urllib.parse.urlparse(url)
        path = parsed_url.path
        if parsed_url.query:
            path = path + '?' + parsed_url.query

        message = (verb + path + str(nonce) + data).encode('utf-8')

        signature = hmac.new(self.user_exchange.secret.encode('utf-8'), message, digestmod=hashlib.sha256).hexdigest()
        return signature

    def __get_auth(self):
        expires = self.generate_nonce()
        return [
            "api-expires: " + str(expires),
            "api-signature: " + self.generate_signature('GET', '/realtime', expires, ''),
            "api-key:" + self.user_exchange.api_key
        ]

    def __on_message(self, message):
        # print(message)
        message = json.loads(message)
        if 'table' not in message:
            return

        table = message['table']
        data = message['data']
        # partial、update
        action = message['action']
        # 钱包数据
        if table == 'wallet':
            for symbol_data in data:
                self.wallet[symbol_data['currency']] = Wallet(account=symbol_data['account'],
                                                              amount=symbol_data['amount']/100000000,
                                                              currency=symbol_data['currency'],
                                                              addr=symbol_data['addr'])
        # 仓位数据
        elif table == 'position':
            for symbol_data in data:
                if action == 'partial':
                    self.position[symbol_data['symbol']] = Position(account=symbol_data['account'],
                                                                    symbol=symbol_data['symbol'],
                                                                    current_qty=symbol_data['currentQty'],
                                                                    current_cost=symbol_data['currentCost'],
                                                                    buy_price=symbol_data['avgCostPrice'],
                                                                    home_notional=symbol_data['homeNotional'])
                elif action == 'update':
                    before_position = self.position[symbol_data['symbol']]
                    if 'currentQty' in symbol_data:
                        before_position.current_qty = symbol_data['currentQty']
                    if 'currentCost' in symbol_data:
                        before_position.current_cost = symbol_data['currentCost']
                    if 'avgCostPrice' in symbol_data:
                        before_position.buy_price = symbol_data['avgCostPrice']
                    if 'homeNotional' in symbol_data:
                        before_position.home_notional = symbol_data['homeNotional']

                    # 更新内存数据
                    self.position[symbol_data['symbol']] = before_position

    def __on_error(self, error):
        if type(error) == ConnectionRefusedError or \
                type(error) == websocket._exceptions.WebSocketConnectionClosedException:
            self.conn.connect()
        else:
            print("其他error!")

    def __on_close(self):
        print("session closed...")

    def __on_open(self):
        print("connection opened...")
        self.conn.send({"op": "subscribe", "args": ["position:XBTUSD", "wallet", "trade:XBTUSD"]})

    # override
    def get_position(self, symbol_info: SymbolInfo) -> Position:
        if symbol_info.symbol_pair in self.position:
            return self.position[symbol_info.symbol_pair]

        return None

    # override
    def get_wallet(self, symbol_info: SymbolInfo) -> Wallet:
        if symbol_info.currency in self.wallet:
            return self.wallet[symbol_info.currency]

        return None
