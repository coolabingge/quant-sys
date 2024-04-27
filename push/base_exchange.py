# coding=utf-8
import time
from threading import Thread

from loguru import logger

from event.event_engine import Event, EventEngine
from realtime.base_realtime import BaseRealTime


class BaseExchange:
    # quotation 行情数据, trade 交易数据
    # 交易所_币种_quotation
    EventType = '%s_%s_quotation'
    PushInterval = 1

    def __init__(self, exchange_name):
        self.__thread_name = "%s_DataThread" % exchange_name
        self.is_active = True
        self.__thread_ready()
        self.init()

    def __thread_ready(self):
        self.quotation_thread = Thread(target=self.push_quotation, name=self.__thread_name)
        self.quotation_thread.setDaemon(True)

    def start(self):
        logger.info("Start Market Data Thread: %s" % self.quotation_thread.name)
        self.quotation_thread.start()

    def stop(self):
        self.is_active = False
        # self.quotation_thread.join()
        self.stop_after()

    def pause(self):
        self.is_active = False

    def resume(self):
        self.is_active = True
        # 重新开始
        self.__thread_ready()
        self.start()

    def stop_after(self):
        # 停止之后做某些事情
        return None

    def push_quotation(self):
        while self.is_active:
            try:
                response_data = self.fetch_quotation()
            except Exception as ex:
                print("push_quotation", ex)
                self.wait()
                continue

            if not response_data:
                self.wait()
                continue

            for one_resp in response_data:
                event = Event(exchange_name=one_resp['exchange_name'],
                              symbol_info=one_resp['symbol_info'],
                              event_type=self.EventType % (one_resp['exchange_name'], one_resp['symbol_info'].symbol_pair_ccxt),
                              data=one_resp['data'])
                if EventEngine().is_start:
                    EventEngine().put(event)
            self.wait()

    def fetch_quotation(self):
        # need child override this method
        return None

    def init(self):
        # do something init
        pass

    def wait(self):
        # for receive quit signal
        for _ in range(int(self.PushInterval) + 1):
            time.sleep(1)

    def name(self):
        # 这里重写返回交易所名称
        return None

    def realtime(self) -> BaseRealTime:
        return None
