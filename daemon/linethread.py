import threading
import time

from loguru import logger

from utils import time_util
from utils.cache_util import CacheUtil
import db.db_sql as db


class LineThread(threading.Thread):

    def __init__(self):
        threading.Thread.__init__(self)

    def run(self) -> None:
        logger.info("Start KLine Storage Thread ...")
        while True:
            logger.info("保存K线数据")
            all_line = CacheUtil().get_all_line()
            for market in all_line:
                market_line = all_line[market]
                for symbol in market_line:
                    symbol_line_dict = market_line[symbol]
                    data_arr = []
                    for time_ux in symbol_line_dict:
                        data_arr.append(symbol_line_dict[time_ux])
                    start_index = len(data_arr) - 300
                    total_index = len(data_arr)
                    symbol_line_latest = data_arr[start_index:total_index]
                    print(market, symbol, time_util.parse(data_arr[total_index - 1][0]/1000))
                    db.insert_line(market, symbol, symbol_line_latest)

            time.sleep(60 * 5)
