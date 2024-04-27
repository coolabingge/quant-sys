from singleton_decorator import singleton

from parse.config import config
from realtime.base_realtime import BaseRealTime


@singleton
class RealTimeEngine(object):
    """
    实时数据处理引擎
    单例，维护用户实时数据
    """
    def __init__(self):
        self.user_rt = dict()

    def start(self, user_id=None, market=None, env=None):
        if (user_id in self.user_rt) and self.user_rt[user_id]:
            return self.user_rt[user_id]
        else:
            return self.__create_instance(user_id, market, env)

    def __create_instance(self, user_id=None, market=None, env=None):
        market_config = config.get_market(market)
        user_exchange = config.get_user(user_id, market, env)

        rt_class = '%sRealTime' % market_config.instance_class
        rt_instance = globals()[rt_class]()

        rt_instance.start(user_exchange)
        self.user_rt[user_id] = rt_instance
        return rt_instance

    def user_engine(self, user_id=None) -> BaseRealTime:
        return self.user_rt[user_id]
