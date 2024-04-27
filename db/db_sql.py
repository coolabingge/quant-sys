# encoding=utf-8
import json

from loguru import logger

import response.error_code as code
import utils.time_util as time_util
from db.mysql_helper import MySqlHelper
from enums.used import RunningStatus
from exception.exception import QuantException
from model.params import DbOrderInfo
from utils import base_utils
from utils.cache_util import RUN_TASK_KEY


def get_quant_config():
    config_sql = "select exchange, currency, symbol, symbol_pair,symbol_pair_ccxt,config from quant_config where symbol_status = 'Enable'"
    cursor, conn, count = MySqlHelper().execute(sql=config_sql, auto_close=True)

    return cursor.fetchall(), count


def get_quant_user_exchange():
    sql = 'select * from quant_user_exchange'

    cursor, conn, count = MySqlHelper().execute(sql=sql, auto_close=True)
    return cursor.fetchall(), count


def get_quant_exchange():
    sql = 'select * from quant_exchange where enable = true'
    cursor, conn, count = MySqlHelper().execute(sql=sql, auto_close=True)

    return cursor.fetchall(), count


def cancel_orders(order_ids=[]):
    if len(order_ids) > 0:
        sql = 'update quant_order_record set status = %s where exchange_order_id in (%s)'
        cancat_condition = ",".join(str(i) for i in order_ids)
        args = ('Cancel', cancat_condition)
        MySqlHelper().update(sql, args)


def insert_start(exchange_name, symbol_info):
    sql = 'insert into quant_task (exchange, symbol_info, status, start_time) ' \
          'values (%s, %s, %s, %s)'

    args = (exchange_name, json.dumps(base_utils.class_to_dict(symbol_info)), 'Running', time_util.now())
    return MySqlHelper().insert_one(sql, args)


def update_quant_running_status(running_id=None, running_status=None):
    sql = 'update quant_task set status = %s, stop_time = %s where id = %s'
    args = (running_status, time_util.now(), running_id)

    MySqlHelper().update(sql, args)


def select_all_quant_task():
    sql = 'select *, CAST(start_time AS CHAR) AS start_time_char from quant_task where status != %s'
    return MySqlHelper().select_all(sql, RunningStatus.Stop.value)

def get_running_task():
    sql = "SELECT a.id, b.user_id, a.symbol_pair, a.strategy_no, a.config, c.name, b.exchange, b.api_key, b.secret, b.passphrase, b.env FROM " \
          "quant_task a, quant_user_exchange b, quant_user c WHERE a.`status` = 'Running' AND a.`ue_id` = b.`id` and a.`user_id` = c.`id`"
    return MySqlHelper().select_all(sql)

def get_quant_task_byid(task_id):
    if not task_id:
        raise QuantException(code.FAIL, "查询任务ID不能为空")

    sql = 'select * from quant_task where id = %s'
    return MySqlHelper().select_one(sql, task_id)


def get_strategy_info(strategy_id=None):
    if not strategy_id:
        return None

    sql = 'select * from quant_strategy where id = %s'
    return MySqlHelper().select_one(sql, strategy_id)


def get_order_summary(user_exchange_id=None, strategy=None):
    sql = 'SELECT SUM(a.amount) AS end_amount, COUNT(0) AS total, SUM(CASE WHEN a.amount <> 0 THEN 1 ELSE 0 END) AS p_win,' \
          'SUM(CASE WHEN a.amount > 0 THEN 1 ELSE 0 END) AS win,' \
          'SUM(CASE WHEN a.amount < 0 THEN 1 ELSE 0 END) AS lose, SUM(a.fee) AS fee FROM (SELECT order_id, ledger_time,SUM(balance) AS balance,' \
          'SUM(fee) AS fee, SUM(amount) AS amount FROM quant_user_ledger WHERE ue_id = %s AND strategy=%s GROUP BY order_id, ledger_time) a'

    return MySqlHelper().select_one(sql, (user_exchange_id, strategy))


def get_day_order_summary(user_exchange_id=None, strategy=None):
    sql = 'SELECT *, CAST(sta_date AS CHAR) AS fmt_date FROM ( ' \
          'SELECT DATE(ledger_time) AS sta_date,COUNT(0) AS total, SUM(amount) AS end_amount, SUM(CASE WHEN a.amount > 0 THEN 1 ELSE 0 END) AS win,' \
          'SUM(CASE WHEN a.amount <> 0 THEN 1 ELSE 0 END) AS p_win, SUM(a.fee) AS fee,' \
          'SUM(CASE WHEN a.amount < 0 THEN 1 ELSE 0 END) AS lose FROM (' \
          'SELECT order_id, ledger_time,SUM(balance) AS balance,' \
          'SUM(fee) AS fee, SUM(amount) AS amount FROM quant_user_ledger WHERE ue_id = %s AND strategy = %s' \
          'GROUP BY order_id, ledger_time) a GROUP BY DATE(ledger_time)) b order by sta_date desc'

    return MySqlHelper().select_all(sql, (user_exchange_id, strategy))


def get_lastest_order(user_exchange_id=None, strategy=None, limit=10):
    sql = 'select *, cast(ledger_time as char) as ledger_fmt_time from quant_user_ledger ' \
          'where ue_id=%s and strategy=%s order by ledger_time desc limit ' + limit

    return MySqlHelper().select_all(sql, (user_exchange_id, strategy))


def get_cache_runnable_task():
    sql = 'select cache_value from quant_cache where cache_key = %s'
    return MySqlHelper().select_one(sql, RUN_TASK_KEY)


def update_runnable_task(task_dict=None):
    if not task_dict:
        return

    sql = 'insert into quant_cache (cache_key, cache_value) values (%s, %s) on duplicate key update cache_value = %s'
    json_value = json.dumps(task_dict)
    return MySqlHelper().execute(sql, (RUN_TASK_KEY, json_value, json_value))


def add_task(body_data=None):
    sql = "insert into quant_task (user_id, ue_id, strategy_no, symbol_pair, config, status, start_time) "\
        "values (%s, %s, %s, %s, %s, %s, now())"

    config_dict = body_data['config']
    for config_key in config_dict:
        config_dict[config_key] = int(config_dict[config_key])

    print(json.dumps(config_dict))
    param = (body_data['userId'], body_data['ueId'], body_data['strategy'],
                 body_data['symbol'], json.dumps(config_dict), 'Running')
    return MySqlHelper().insert_one(sql, param)


def runntask_by_id(task_id=None):
    sql = "SELECT a.status, a.id, b.user_id, a.symbol_pair, a.strategy_no, a.config, c.name, b.exchange, b.api_key, b.secret, b.passphrase, b.env FROM " \
          "quant_task a, quant_user_exchange b, quant_user c WHERE a.`ue_id` = b.`id` and a.`user_id` = c.`id` and a.id = %s"
    return MySqlHelper().select_one(sql, task_id)


def disable_task(task_id=None):
    sql = "update quant_task set status = 'Stop' where id = %s"
    MySqlHelper().update(sql, task_id)


def run_task(task_id=None):
    sql = "update quant_task set status = 'Running' where id = %s"
    MySqlHelper().update(sql, task_id)


def page_task(status='Running'):
    sql = "SELECT a.status, a.id, b.user_id, a.symbol_pair, a.strategy_no, a.config, c.name, b.exchange, b.api_key, b.secret, b.passphrase, b.env FROM " \
          "quant_task a, quant_user_exchange b, quant_user c WHERE a.status = %s and a.`ue_id` = b.`id` and a.`user_id` = c.`id`"

    return MySqlHelper().select_all(sql, status)


def all_users():
    sql = "select * from quant_user"
    return MySqlHelper().select_all(sql)


def all_market_account(user_id=None):
    sql = "select id, user_id, user_name, env, exchange from quant_user_exchange where user_id = %s"
    return MySqlHelper().select_all(sql, user_id)


def market_default_config(exchange=None, currency=None):
    sql = "select config from quant_config where exchange=%s and currency = %s"
    return MySqlHelper().select_all(sql, exchange, currency)


def all_symbols(ue_id=None):
    sql = "SELECT a.currency,a.symbol,a.`exchange` FROM quant_config a, quant_user_exchange b WHERE  " \
          " a.`symbol_status` = 'Enable' AND b.id = %s AND a.`exchange` = b.`exchange`"
    return MySqlHelper().select_all(sql, ue_id)


def all_strategies():
    sql = "select * from quant_strategy"
    return MySqlHelper().select_all(sql)


def batch_insert_orders(orders=None):
    if not orders:
        return

    sql = 'insert into quant_orders(ue_id, symbol_pair, client_oid, size, create_time, filled_qty, ' \
          'fee, order_id, price, price_avg, type, contract_val, order_type, state, trigger_price, leverage, ' \
          'insert_time) ' \
          'values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,now())'

    MySqlHelper().insert_many(sql, orders)


def batch_insert_ledgers(ledgers=None):
    if not ledgers:
        return

    sql = 'insert into quant_user_ledger(ue_id, symbol_pair, balance, currency, instrument_id, ' \
          'order_id, fee, ledger_id, ledger_time, type, insert_time, amount, strategy, env) values ' \
          '(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,now(),%s,%s,%s)'

    MySqlHelper().insert_many(sql, ledgers)


def get_max_ledger_id(ue_id=None):
    sql = 'select max(ledger_id) as from_id from quant_user_ledger where ue_id = %s'
    rst = MySqlHelper().select_one(sql, ue_id)
    if rst and rst['from_id']:
        return rst['from_id']
    else:
        return None


def insert_order(db_order_info: DbOrderInfo):
    sql = 'insert into quant_order_record (exchange, symbol, symbol_pair, order_price, ' \
          'order_usdt, other_money, local_order_time, exchange_order_id, exchange_order_time, ' \
          'side, order_type, status, open_type, side_price, profit_rate, profit_price, side_time) ' \
          'values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)'

    args = (
        db_order_info.exchange,
        db_order_info.symbol_info.symbol,
        db_order_info.symbol_info.symbol_pair,
        db_order_info.order_price,
        db_order_info.order_usdt,
        db_order_info.other_money,
        time_util.now(),
        db_order_info.exchange_order_id,
        db_order_info.exchange_order_time,
        db_order_info.side,
        db_order_info.order_type,
        db_order_info.status,
        db_order_info.open_type,
        db_order_info.sell_price,
        db_order_info.profit_rate,
        db_order_info.profit_price,
        time_util.now(),
    )
    MySqlHelper().insert_one(sql, args)

def insert_line(market=None, symbol=None, lines=None):
    if not lines:
        logger.info("K线数据为空，无法持久化，平台：%s，币对：%s" % (market, symbol))
        return

    sql = 'insert into quant_line (market, symbol, open_time, line_open, high, low, line_close, volume, update_time) values '
    for line in lines:
        time_parse = time_util.parse(line[0]/1000)
        sql += '(\"%s\",\"%s\",\"%s\", %s,%s,%s,%s,%s,\"%s\"),' % (market, symbol, time_parse, line[1], line[2],  line[3], line[4], line[5], time_util.now())

    sql = sql[:-1]
    sql += " ON DUPLICATE KEY UPDATE line_open = VALUES(line_open), high = VALUES(high), low = VALUES(low), line_close = VALUES(line_close), volume = VALUES(volume), update_time = NOW()"
    MySqlHelper().execute(sql)


def max_line_time(market=None, symbol=None):
    sql = "SELECT UNIX_TIMESTAMP(MAX(open_time)) AS max_uxtime, MAX(open_time) AS max_strtime FROM quant_line WHERE market = %s AND symbol = %s"
    return MySqlHelper().select_one(sql, (market, symbol))


def get_history_line(market=None, symbol=None, start_time=None):
    sql = "select cast(open_time as char) as  open_time, CAST(line_open AS CHAR) AS line_open, high, low, line_close, volume from quant_line where market = %s and symbol = %s and open_time >= %s order by open_time asc"
    logger.info("Cache StartTime: %s" % start_time)
    return MySqlHelper().select_all(sql, (market, symbol, start_time))
