import base64
import datetime
import hmac
import json

import pytz
import requests

# http header
from constants.constant import USE_PROXY, PROXIES, API_ENV
from enums.used import Env
from exception.exception import QuantException

API_URL = 'https://www.okex.com'
CONTENT_TYPE = 'Content-Type'
OK_ACCESS_KEY = 'OK-ACCESS-KEY'
OK_ACCESS_SIGN = 'OK-ACCESS-SIGN'
OK_ACCESS_TIMESTAMP = 'OK-ACCESS-TIMESTAMP'
OK_ACCESS_PASSPHRASE = 'OK-ACCESS-PASSPHRASE'
OK_ENV = 'x-simulated-trading'

ACEEPT = 'Accept'
COOKIE = 'Cookie'
LOCALE = 'Locale='

APPLICATION_JSON = 'application/json'

GET = "GET"
POST = "POST"
DELETE = "DELETE"

SERVER_TIMESTAMP_URL = '/api/general/v3/time'

# account

CURRENCIES_INFO = '/api/account/v3/currencies'
WALLET_INFO = '/api/account/v3/wallet'
CURRENCY_INFO = '/api/account/v3/wallet/'
COIN_TRANSFER = '/api/account/v3/transfer'
COIN_WITHDRAW = '/api/account/v3/withdrawal'
COIN_FEE = '/api/account/v3/withdrawal/fee'
COINS_WITHDRAW_RECORD = '/api/account/v3/withdrawal/history'
COIN_WITHDRAW_RECORD = '/api/account/v3/withdrawal/history/'
LEDGER_RECORD = '/api/account/v3/ledger'
TOP_UP_ADDRESS = '/api/account/v3/deposit/address'
COIN_TOP_UP_RECORDS = '/api/account/v3/deposit/history'
COIN_TOP_UP_RECORD = '/api/account/v3/deposit/history/'

# spot
SPOT_ACCOUNT_INFO = '/api/spot/v3/accounts'
SPOT_COIN_ACCOUNT_INFO = '/api/spot/v3/accounts/'
SPOT_LEDGER_RECORD = '/api/spot/v3/accounts/'
SPOT_ORDER = '/api/spot/v3/orders'
SPOT_ORDERS = '/api/spot/v3/batch_orders'
SPOT_REVOKE_ORDER = '/api/spot/v3/cancel_orders/'
SPOT_REVOKE_ORDERS = '/api/spot/v3/cancel_batch_orders/'
SPOT_ORDERS_LIST = '/api/spot/v3/orders'
SPOT_ORDERS_PENDING = '/api/spot/v3/orders_pending'
SPOT_ORDER_INFO = '/api/spot/v3/orders/'
SPOT_FILLS = '/api/spot/v3/fills'
SPOT_COIN_INFO = '/api/spot/v3/instruments'
SPOT_DEPTH = '/api/spot/v3/instruments/'
SPOT_TICKER = '/api/spot/v3/instruments/ticker'
SPOT_SPECIFIC_TICKER = '/api/spot/v3/instruments/'
SPOT_DEAL = '/api/spot/v3/instruments/'
SPOT_KLINE = '/api/spot/v3/instruments/'

# lever
LEVER_ACCOUNT = '/api/margin/v3/accounts'
LEVER_COIN_ACCOUNT = '/api/margin/v3/accounts/'
LEVER_LEDGER_RECORD = '/api/margin/v3/accounts/'
LEVER_CONFIG = '/api/margin/v3/accounts/availability'
LEVER_SPECIFIC_CONFIG = '/api/margin/v3/accounts/'
LEVER_BORROW_RECORD = '/api/margin/v3/accounts/'
LEVER_SPECIFIC_BORROW_RECORD = '/api/margin/v3/accounts/'
LEVER_BORROW_COIN = '/api/margin/v3/accounts/borrow'
LEVER_REPAYMENT_COIN = '/api/margin/v3/accounts/repayment'
LEVER_ORDER = '/api/margin/v3/orders'
LEVER_ORDERS = '/api/margin/v3/batch_orders'
LEVER_REVOKE_ORDER = '/api/margin/v3/cancel_orders/'
LEVER_REVOKE_ORDERS = '/api/margin/v3/cancel_batch_orders'
LEVER_ORDER_LIST = '/api/margin/v3/orders'
LEVEL_ORDERS_PENDING = '/api/margin/v3/orders_pending'
LEVER_ORDER_INFO = '/api/margin/v3/orders/'
LEVER_FILLS = '/api/margin/v3/fills'
FF = '/api/futures/v3/orders'

# future
FUTURE_POSITION = '/api/futures/v3/position'
FUTURE_SPECIFIC_POSITION = '/api/futures/v3/'
FUTURE_ACCOUNTS = '/api/futures/v3/accounts'
FUTURE_COIN_ACCOUNT = '/api/futures/v3/accounts/'
FUTURE_GET_LEVERAGE = '/api/futures/v3/accounts/'
FUTURE_SET_LEVERAGE = '/api/futures/v3/accounts/'
FUTURE_LEDGER = '/api/futures/v3/accounts/'
FUTURE_DELETE_POSITION = '/api/futures/v3/close_all_orders'
FUTURE_ORDER = '/api/futures/v3/order'
FUTURE_ORDERS = '/api/futures/v3/orders'
FUTURE_REVOKE_ORDER = '/api/futures/v3/cancel_order/'
FUTURE_REVOKE_ORDERS = '/api/futures/v3/cancel_batch_orders/'
FUTURE_ORDERS_LIST = '/api/futures/v3/orders'
FUTURE_ORDER_INFO = '/api/futures/v3/orders/'
FUTURE_FILLS = '/api/futures/v3/fills'
FUTURE_PRODUCTS_INFO = '/api/futures/v3/instruments'
FUTURE_DEPTH = '/api/futures/v3/instruments/'
FUTURE_TICKER = '/api/futures/v3/instruments/ticker'
FUTURE_SPECIFIC_TICKER = '/api/futures/v3/instruments/'
FUTURE_TRADES = '/api/futures/v3/instruments/'
FUTURE_KLINE = '/api/futures/v3/instruments/'
FUTURE_INDEX = '/api/futures/v3/instruments/'
FUTURE_RATE = '/api/futures/v3/rate'
FUTURE_ESTIMAT_PRICE = '/api/futures/v3/instruments/'
FUTURE_HOLDS = '/api/futures/v3/instruments/'
FUTURE_LIMIT = '/api/futures/v3/instruments/'
FUTURE_LIQUIDATION = '/api/futures/v3/instruments/'
FUTURE_MARK = '/api/futures/v3/instruments/'
HOLD_AMOUNT = '/api/futures/v3/accounts/'
# CURRENCY_LIST = '/api/futures/v3/instruments/currencies/'

# ETT
ETT_ACCOUNTS = '/api/ett/v3/accounts'
ETT_ACCOUNT = '/api/ett/v3/accounts/'
ETT_LEDGER = '/api/ett/v3/accounts/'
ETT_ORDER = '/api/ett/v3/orders'
ETT_REVOKE = '/api/ett/v3/orders/'
ETT_ORDER_LIST = '/api/ett/v3/orders'
ETT_SPECIFIC_ORDER = '/api/ett/v3/orders/'
ETT_CONSTITUENTS = '/api/ett/v3/constituents/'
ETT_DEFINE = '/api/ett/v3/define-price/'

# SWAP
SWAP_POSITIONS = '/api/swap/v3/position'
SWAP_POSITION = '/api/swap/v3/'
SWAP_ACCOUNTS = '/api/swap/v3/accounts'
SWAP_ACCOUNT = '/api/swap/v3/'
SWAP_ORDER = '/api/swap/v3/order'
SWAP_ORDERS = '/api/swap/v3/orders'
SWAP_CANCEL_ORDER = '/api/swap/v3/cancel_order/'
SWAP_CANCEL_ORDERS = '/api/swap/v3/cancel_batch_orders/'
SWAP_FILLS = '/api/swap/v3/fills'
SWAP_INSTRUMENTS = '/api/swap/v3/instruments'
SWAP_TICKETS = '/api/swap/v3/instruments/ticker'
SWAP_RATE = '/api/swap/v3/rate'
SWAP_ORDER_ALGO = '/api/swap/v3/order_algo'
SWAP_CLOSE_POSITIONS = '/api/swap/v3/close_position'


class OkexClient(object):

    def __init__(self, api_key, api_seceret_key, passphrase, use_server_time=False, env: Env = None):

        self.API_KEY = api_key
        self.API_SECRET_KEY = api_seceret_key
        self.PASSPHRASE = passphrase
        self.use_server_time = use_server_time
        self.env = env

    def _request(self, method, request_path, params, cursor=False):

        if method == GET:
            request_path = request_path + OkexClient.parse_params_to_str(params)
        # url
        url = API_URL + request_path

        timestamp = OkexClient.get_timestamp_utc0()
        # sign & header
        if self.use_server_time:
            timestamp = self._get_timestamp()
        body = json.dumps(params) if method == POST else ""

        sign = OkexClient.sign(OkexClient.pre_hash(timestamp, method, request_path, str(body)), self.API_SECRET_KEY)
        header = self._get_header(self.API_KEY, sign, timestamp, self.PASSPHRASE)

        # send request
        response = None
        if not (API_ENV == 'EnvNormal'):
            # print("url:", url)
            # print("headers:", header)
            # print("body:", body)
            None

        proxies = PROXIES if USE_PROXY else None
        if method == GET:
            response = requests.get(url, headers=header, proxies=proxies)
        elif method == POST:
            response = requests.post(url, data=body, headers=header, proxies=proxies)
            # response = requests.post(url, json=body, headers=header)
        elif method == DELETE:
            response = requests.delete(url, headers=header, proxies=proxies)

        # exception handle
        if not str(response.status_code).startswith('2'):
            raise QuantException(message=response.json())
        try:
            res_header = response.headers
            if cursor:
                r = dict()
                try:
                    r['before'] = res_header['OK-BEFORE']
                    r['after'] = res_header['OK-AFTER']
                except:
                    print("")
                return response.json(), r
            else:
                return response.json()
        except ValueError:
            print('Invalid Response: %s' % response.text)
            raise QuantException('Invalid Response: %s' % response.text)

    def _request_without_params(self, method, request_path):
        return self._request(method, request_path, {})

    def _request_with_params(self, method, request_path, params, cursor=False):
        return self._request(method, request_path, params, cursor)

    def _get_timestamp(self):
        url = API_URL + SERVER_TIMESTAMP_URL
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()['iso']
        else:
            return ""

    @staticmethod
    def sign(message, secretKey):
        mac = hmac.new(bytes(secretKey, encoding='utf8'), bytes(message, encoding='utf-8'), digestmod='sha256')
        d = mac.digest()
        return base64.b64encode(d)

    @staticmethod
    def pre_hash(timestamp, method, request_path, body):
        return str(timestamp) + str.upper(method) + request_path + body

    def _get_header(self, api_key, sign, timestamp, passphrase):
        header = dict()
        header[CONTENT_TYPE] = APPLICATION_JSON
        header[OK_ACCESS_KEY] = api_key
        header[OK_ACCESS_SIGN] = sign
        header[OK_ACCESS_TIMESTAMP] = str(timestamp)
        header[OK_ACCESS_PASSPHRASE] = passphrase
        if self.env and (self.env == Env.Test):
            header[OK_ENV] = "1"

        return header

    @staticmethod
    def parse_params_to_str(params):
        url = '?'
        for key, value in params.items():
            url = url + str(key) + '=' + str(value) + '&'

        return url[0:-1]

    @staticmethod
    def get_timestamp():
        now = datetime.datetime.now()
        t = now.isoformat("T", "milliseconds")
        return t + "Z"

    @staticmethod
    def get_timestamp_utc0():
        utc_tz = pytz.timezone('UTC')
        now = datetime.datetime.now(utc_tz)
        t = now.isoformat("T", "milliseconds")
        if '+00:00' in t:
            t = t.replace('+00:00', '')
        return t + "Z"

    @staticmethod
    def signature(timestamp, method, request_path, body, secret_key):
        if str(body) == '{}' or str(body) == 'None':
            body = ''
        message = str(timestamp) + str.upper(method) + request_path + str(body)
        mac = hmac.new(bytes(secret_key, encoding='utf8'), bytes(message, encoding='utf-8'), digestmod='sha256')
        d = mac.digest()
        return base64.b64encode(d)

    def get_position(self):
        return self._request_without_params(GET, SWAP_POSITIONS)

    def get_currency(self, symbol):
        return self._request_without_params(GET, CURRENCY_INFO + str(symbol))

    def get_specific_position(self, instrument_id):
        return self._request_without_params(GET, SWAP_POSITION + str(instrument_id) + '/position')

    def get_accounts(self):
        return self._request_without_params(GET, SWAP_ACCOUNTS)

    def get_coin_account(self, instrument_id):
        return self._request_without_params(GET, SWAP_ACCOUNT + str(instrument_id) + '/accounts')

    def get_settings(self, instrument_id):
        return self._request_without_params(GET, SWAP_ACCOUNTS + '/' + str(instrument_id) + '/settings')

    def set_leverage(self, instrument_id, leverage, side):
        params = dict()
        params['leverage'] = str(leverage)
        params['side'] = str(side)
        return self._request_with_params(POST, SWAP_ACCOUNTS + '/' + str(instrument_id) + '/leverage', params)

    def get_ledger(self, instrument_id, froms='', to='', limit='500'):
        """
        获取账单流水
        :param instrument_id:
        :param froms:
        :param to:
        :param limit:
        :return:
        """
        params = {}
        if froms:
            params['before'] = froms
        if to:
            params['after'] = to
        if limit:
            params['limit'] = limit
        return self._request_with_params(GET, SWAP_ACCOUNTS + '/' + str(instrument_id) + '/ledger', params)

    def take_order(self, instrument_id, size, otype, price, client_oid, match_price, order_type):
        params = {'instrument_id': instrument_id, 'size': size, 'type': otype, 'price': price, 'order_type': order_type}
        if client_oid:
            params['client_oid'] = client_oid
        if match_price:
            params['match_price'] = match_price
        return self._request_with_params(POST, SWAP_ORDER, params)

    def take_orders(self, order_data, instrument_id):
        params = {'instrument_id': instrument_id, 'order_data': order_data}
        return self._request_with_params(POST, SWAP_ORDERS, params)

    def revoke_order(self, order_id='', client_oid='', instrument_id='BTC-USD-SWAP'):
        if order_id:
            return self._request_without_params(POST, SWAP_CANCEL_ORDER + str(instrument_id) + '/' + str(order_id))
        elif client_oid:
            return self._request_without_params(POST, SWAP_CANCEL_ORDER + str(instrument_id) + '/' + str(client_oid))

    def revoke_orders(self, ids='', client_oids='', instrument_id=''):
        if ids:
            params = {'ids': ids}
        elif client_oids:
            params = {'client_oids': client_oids}
        return self._request_with_params(POST, SWAP_CANCEL_ORDERS + str(instrument_id), params)

    def get_order_list(self, status, instrument_id, froms='', to='', limit=''):
        params = {'status': status}
        if froms:
            params['from'] = froms
        if to:
            params['to'] = to
        if limit:
            params['limit'] = limit
        return self._request_with_params(GET, SWAP_ORDERS + '/' + str(instrument_id), params)

    def get_order_info(self, instrument_id='', order_id='', client_oid=''):
        if order_id:
            return self._request_without_params(GET, SWAP_ORDERS + '/' + str(instrument_id) + '/' + str(order_id))
        elif client_oid:
            return self._request_without_params(GET, SWAP_ORDERS + '/' + str(instrument_id) + '/' + str(client_oid))

    def get_fills(self, order_id='', client_oid='', instrument_id='', froms='', to='', limit=''):
        if order_id:
            params = {'order_id': order_id, 'instrument_id': instrument_id}
        if client_oid:
            params = {'client_oid': client_oid, 'instrument_id': instrument_id}
        if froms:
            params['from'] = froms
        if to:
            params['to'] = to
        if limit:
            params['limit'] = limit
        return self._request_with_params(GET, SWAP_FILLS, params)

    def get_instruments(self):
        return self._request_without_params(GET, SWAP_INSTRUMENTS)

    def get_depth(self, instrument_id, size):
        if size:
            params = {'size': size}
            return self._request_with_params(GET, SWAP_INSTRUMENTS + '/' + str(instrument_id) + '/depth', params)
        return self._request_without_params(GET, SWAP_INSTRUMENTS + '/' + str(instrument_id) + '/depth')

    def get_ticker(self):
        return self._request_without_params(GET, SWAP_TICKETS)

    def get_specific_ticker(self, instrument_id):
        return self._request_without_params(GET, SWAP_INSTRUMENTS + '/' + str(instrument_id) + '/ticker')

    def get_trades(self, instrument_id, froms='', to='', limit=''):
        params = {}
        if froms:
            params['from'] = froms
        if to:
            params['to'] = to
        if limit:
            params['limit'] = limit
        return self._request_with_params(GET, SWAP_INSTRUMENTS + '/' + str(instrument_id) + '/trades', params)

    def get_kline(self, instrument_id, granularity, start, end):
        params = {}
        if granularity:
            params['granularity'] = granularity
        if start:
            params['start'] = start
        if end:
            params['end'] = end
        return self._request_with_params(GET, SWAP_INSTRUMENTS + '/' + str(instrument_id) + '/candles', params)

    def get_algo_orders(self, instrument_id=None):
        params = dict()
        # 1：待生效
        # 2：已生效
        # 3：已撤销
        # 4：部分生效
        # 5：暂停生效
        # 6：委托失败
        params['order_type'] = 0
        params['status'] = 2
        return self._request_with_params(GET, SWAP_ORDER_ALGO + '/' + str(instrument_id), params)

    def get_index(self, instrument_id):
        return self._request_without_params(GET, SWAP_INSTRUMENTS + '/' + str(instrument_id) + '/index')

    def get_rate(self):
        return self._request_without_params(GET, SWAP_RATE)

    def get_holds(self, instrument_id):
        return self._request_without_params(GET, SWAP_INSTRUMENTS + '/' + str(instrument_id) + '/open_interest')

    def get_limit(self, instrument_id):
        return self._request_without_params(GET, SWAP_INSTRUMENTS + '/' + str(instrument_id) + '/price_limit')

    def get_liquidation(self, instrument_id, status, froms='', to='', limit=''):
        params = {'status': status}
        if froms:
            params['from'] = froms
        if to:
            params['to'] = to
        if limit:
            params['limit'] = limit
        return self._request_with_params(GET, SWAP_INSTRUMENTS + '/' + str(instrument_id) + '/liquidation', params)

    def get_holds_amount(self, instrument_id):
        return self._request_without_params(GET, SWAP_ACCOUNTS + '/' + str(instrument_id) + '/holds')

    def get_funding_time(self, instrument_id):
        return self._request_without_params(GET, SWAP_INSTRUMENTS + '/' + str(instrument_id) + '/funding_time')

    def get_mark_price(self, instrument_id):
        return self._request_without_params(GET, SWAP_INSTRUMENTS + '/' + str(instrument_id) + '/mark_price')

    def get_historical_funding_rate(self, instrument_id, froms='', to='', limit=''):
        params = {}
        if froms:
            params['from'] = froms
        if to:
            params['to'] = to
        if limit:
            params['limit'] = limit
        return self._request_with_params(GET, SWAP_INSTRUMENTS + '/' + str(instrument_id) + '/historical_funding_rate',
                                         params)

    def close_position(self, instrument_id=None, direction=None):
        params = dict()
        params['instrument_id'] = instrument_id
        params['direction'] = direction
        return self._request_with_params(POST, SWAP_CLOSE_POSITIONS, params)
