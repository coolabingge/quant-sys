import json
import ssl
import threading
from time import sleep

import websocket
import constants.constant as const

from exception.exception import QuantException


class Proxy(object):

    def __init__(self, proxy_ip=None, proxy_port=None):
        self.proxy_ip = proxy_ip
        self.proxy_port = proxy_port


class Conn(object):

    def __init__(self, ws_url=None, proxy: Proxy = None, on_message=None, on_error=None, on_close=None, on_open=None,
                 header=None):
        self.on_message = on_message
        self.on_error = on_error
        self.on_close = on_close
        self.on_open = on_open
        self.header = header
        if const.USE_PROXY:
            self.proxy = proxy
        else:
            self.proxy = None
        self.ws_url = ws_url
        self.closed = False

        self.__ready_websocket()

    def __ready_websocket(self):
        websocket.enableTrace(True)
        self.ws_client = websocket.WebSocketApp(self.ws_url,
                                                on_message=self.on_message,
                                                on_error=self.on_error,
                                                on_close=self.on_close,
                                                on_open=self.on_open,
                                                header=self.header)

    def send(self, data: dict = None):
        if data:
            self.ws_client.send(json.dumps(data))
        else:
            print("data type not supported...")

    def __run(self):
        if self.proxy:
            self.ws_client.run_forever(http_proxy_host=self.proxy.proxy_ip,
                                       http_proxy_port=self.proxy.proxy_port,
                                       sslopt={"cert_reqs": ssl.CERT_NONE},
                                       ping_interval=15,
                                       ping_timeout=5)
        else:
            self.ws_client.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE}, ping_interval=15, ping_timeout=5)

    def close(self):
        self.closed = True
        self.ws_client.close()

    def connect(self):
        self.wst = threading.Thread(target=lambda: self.__run())
        self.wst.daemon = True
        self.wst.start()

        conn_timeout = 5
        while not self.ws_client.sock or not self.ws_client.sock.connected and conn_timeout:
            sleep(1)
            conn_timeout -= 1

        if not conn_timeout:
            self.close()
            raise QuantException(message='Couldn\'t connect to WS! Closing.')

# def on_open(ws):
#     print("============= open ================")
#
# def on_message(ws, message):
#     print(message)
#     f = gzip.decompress(message)
#     print(str(f, encoding="utf-8"))
#
# from io import BytesIO
# import gzip
#
# conn = Conn(ws_url="wss://ws-app.cicadafitness.com/market", on_open=on_open, on_message=on_message, header=[
#     "Sec-WebSocket-Extensions: permessage-deflate; client_max_window_bits",
#     "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36"
# ])
# conn.connect()
# conn.send(json.dumps(
#     {"dataType": "market.tradeDetail.btc_usdt", "id": "5f919b4e6487d", "reqType": "sub"}))
#
# conn.send(json.dumps(
#     {"api": "api/market/v1/kline", "period": "1min", "coinName": "btc", "valuationCoinName": "usdt", "exchangeId": 2,
#      "pagingSize": 1, "id": "5f918fa601c6a", "reqType": "req",
#      "valuationCoinName": "usdt"}))
