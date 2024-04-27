from loguru import logger
from singleton_decorator import singleton

RUN_TASK_KEY = 'RunTaskInfo'
# 行情 任务ID
REALTIME_QUOTA = 'RealTimeQuota_%s'


@singleton
class CacheUtil(object):

    def __init__(self):
        self.cache_obj = {}
        self.line_cache = {}

    def set(self, key=None, value=None):
        self.cache_obj[key] = value

    def get(self, key=None):
        if key in self.cache_obj:
            return self.cache_obj[key]

        return None

    def set_line(self, market=None, symbol=None, line_data=None):
        try:
            # logger.info("market: %s, symbol: %s, line_data: %s" % (market, symbol, line_data))
            market_line = {}
            symbol_line = {}

            if market in self.line_cache:
                market_line = self.line_cache[market]
            else:
                self.line_cache[market] = {}

            if symbol in market_line:
                symbol_line = market_line[symbol]
            else:
                self.line_cache[market][symbol] = {}

            line_dict_data = {}
            if isinstance(line_data, dict):
                line_dict_data = line_data
            else:
                for line in line_data:
                    line_dict_data[line[0]] = line

            if line_data:
                symbol_line.update(line_dict_data)
                # logger.info("更新长度: %s" % (len(symbol_line)))
                self.line_cache[market][symbol] = symbol_line
        except Exception as ex:
            print(ex)

    def get_line(self, market=None, symbol=None):
        return self.line_cache[market][symbol]

    def get_all_line(self):
        return self.line_cache
