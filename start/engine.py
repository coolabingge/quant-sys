import json

from loguru import logger
from singleton_decorator import singleton

import db.db_sql as db
from enums.used import Env
from user.user_engine import UserRunEngine


@singleton
class StartEngine(object):
    """
    启动引擎类
    """
    _instance = None

    def __init__(self):
        self.bitmex = None
        self.okex = None

    # 启动交易所执行策略
    def action_new_task(self, user_id=None, strategy=1, body_data=None):
        task_id = db.add_task(body_data)
        task_obj = db.runntask_by_id(task_id)
        UserRunEngine(task_obj['exchange'],
                      user_id,
                      env=Env.Dist if task_obj['env'] == 'Dist' else Env.Test,
                      strategy=strategy,
                      task_config=json.loads(task_obj['config']),
                      task_id=task_obj['id'],
                      symbol=task_obj['symbol_pair'],
                      task_obj=task_obj).start()
        logger.info("开启用户策略执行，用户ID：%s，环境：%s, 交易所：%s,执行策略：%s" % (user_id, task_obj['env'], task_obj['exchange'], strategy))

    def action_stop_task(self, task_id):
        db.disable_task(task_id)

    def action_restart_task(self, task_id):
        task_obj = db.runntask_by_id(task_id)
        if task_obj['status'] != 'Running':
            UserRunEngine(market=task_obj['exchange'],
                          user_id=task_obj['user_id'],
                          env=Env.Dist if task_obj['env'] == 'Dist' else Env.Test,
                          strategy=task_obj['strategy_no'],
                          task_config=json.loads(task_obj['config']),
                          task_id=task_obj['id'],
                          symbol=task_obj['symbol_pair'],
                          task_obj=task_obj).start()

            db.run_task(task_id)
