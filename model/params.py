"""
symbol=self.symbol_dict_transfer[params['symbol']],
                side=Side.Buy.value,
                ordType=OrderType.Limit.value,
                price=price,
                orderQty=qty).result()
"""
from enums.used import Side, OrderType, OpenType
from event.event_engine import SymbolInfo


class OrderCreateParams(object):

    def __init__(self, side: Side = None, order_type: OrderType = OrderType.Limit, price=None,
                 order_qty=None, win_rate=None, status=None, client_oid=None):
        self.side = side
        self.order_type = order_type
        self.price = price
        self.order_qty = order_qty
        self.win_rate = win_rate
        self.status = status
        self.client_oid = client_oid


class DbOrderInfo(object):

    def __init__(self, exchange=None,
                 symbol_info: SymbolInfo = None,
                 order_price=None,
                 order_usdt=None,
                 other_money=0,
                 exchange_order_id=None,
                 exchange_order_time=None,
                 side=None,
                 order_type=None,
                 status='open',
                 open_type: OpenType = OpenType.Much,
                 sell_price=None,
                 profit_rate=None,
                 profit_price=None):
        self.exchange = exchange
        self.symbol_info = symbol_info
        self.order_price = order_price
        self.order_usdt = order_usdt
        self.other_money = other_money
        self.exchange_order_id = exchange_order_id
        self.exchange_order_time = exchange_order_time
        self.side = side
        self.order_type = order_type
        self.status = status
        self.open_type = open_type.value
        self.sell_price = sell_price
        self.profit_rate = profit_rate
        self.profit_price = profit_price


class Position(object):

    def __init__(self, account=None, symbol=None, leverage=None, current_qty=None, current_cost=None, buy_price=None,
                 home_notional=None, direction=None):
        self.symbol = symbol
        self.account = account
        self.leverage = leverage
        self.current_qty = current_qty
        self.current_cost = current_cost
        self.buy_price = buy_price
        self.home_notional = home_notional
        # 仓位类型，多/空
        self.direction = direction


class Wallet(object):

    def __init__(self, account=None, amount=None, currency=None, addr=None, used=None):
        self.account = account
        # 总量
        self.amount = float(amount)
        self.currency = currency
        self.addr = addr
        # 使用量（持仓量）
        self.used = float(used)
        self.position_rate = float(used) / float(amount)


class QuantExchange(object):

    def __init__(self, exchange_name=None, exchange=None, instance_class=None, api_dist_http=None,
                 api_dist_websocket=None, api_test_http=None, api_test_websocket=None):
        self.exchange_name = exchange_name
        self.exchange = exchange
        self.api_dist_http = api_dist_http
        self.api_dist_websocket = api_dist_websocket
        self.api_test_http = api_test_http
        self.api_test_websocket = api_test_websocket
        self.instance_class = instance_class


class QuantUserExchange(object):

    def __init__(self, user_id=None, exchange=None, api_key=None, secret=None, passphrase=None, env=None, ue_id=None, user_name=None):
        self.ue_id = ue_id
        self.user_id = user_id
        self.user_name = user_name
        self.exchange = exchange
        self.api_key = api_key
        self.secret = secret
        self.passphrase = passphrase
        self.env = env


class OrderResp(object):

    def __init__(self, order_id=None, success=True):
        self.order_id = order_id
        self.success = success
