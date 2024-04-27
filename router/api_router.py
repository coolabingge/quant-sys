import json
from pprint import pprint

from flask import jsonify, request, Blueprint
from loguru import logger

import db.db_sql as db
from event.event_engine import SymbolInfo
from exception.exception import QuantException
from realtime.bitmex_realtime import BitMexRealTime
from response.result_resp import ResultResp
from start.engine import StartEngine
from utils.cache_util import CacheUtil, REALTIME_QUOTA

api = Blueprint('api', __name__)


@api.after_request
def cors(environ):
    environ.headers['Access-Control-Allow-Origin'] = '*'
    environ.headers['Access-Control-Allow-Method'] = '*'
    environ.headers['Access-Control-Allow-Headers'] = 'x-requested-with,content-type'
    return environ


@api.errorhandler(QuantException)
def handle_invalid_usage(error):
    print(error)
    return jsonify(ResultResp().failed())


@api.route('/stats', methods=["GET"])
def index():
    return jsonify(ResultResp().ok())


@api.route('/data/users', methods=["GET"])
def list_all_users():
    return jsonify(ResultResp().ok(data=db.all_users()))


@api.route('/data/market_accounts/<int:user_id>', methods=["GET"])
def list_market_accounts(user_id):
    return jsonify(ResultResp().ok(data=db.all_market_account(user_id)))


@api.route('/data/symbols/<int:ue_id>', methods=["GET"])
def list_all_symbols(ue_id):
    return jsonify(ResultResp().ok(data=db.all_symbols(ue_id)))


@api.route('/data/strategies', methods=["GET"])
def list_all_strategies():
    return jsonify(ResultResp().ok(data=db.all_strategies()))


@api.route('/data/symbol_config', methods=["GET"])
def get_symbol_config():
    market = request.args['market'] or 'OKEX'
    symbol = request.args['symbol'] or 'BTC-USDT-SWAP'
    return jsonify(ResultResp().ok(data=db.market_default_config(market, symbol)))


@api.route('/action/newTask', methods=["POST"])
def task_action_new():
    """
    策略行为
    body {
        "symbol": BTC/ETH， // 币种
        "userId": # 用户ID, // 用户ID
        "ueId": "Dist", // 用户交易市场ID
        "strategy": 1, // 策略编号
        "config": {}  // 策略配置
    }
    :return:
    """
    body_json = json.loads(request.get_data().decode('utf-8'))
    if body_json:
        StartEngine().action_new_task(
            user_id=body_json['userId'],
            strategy=body_json['strategy'],
            body_data=body_json)

    return jsonify(ResultResp().ok())


@api.route('/action/stopTask/<int:task_id>', methods=["GET"])
def task_action_stop(task_id):
    StartEngine().action_stop_task(task_id)
    return jsonify(ResultResp().ok())


@api.route('/action/restartTask/<int:task_id>', methods=["GET"])
def task_action_restart(task_id):
    StartEngine().action_restart_task(task_id)
    return jsonify(ResultResp().ok())


@api.route('/task/list', methods=["GET"])
def get_task_list():
    status = request.args['status'] or 'Running'
    return jsonify(ResultResp().ok(data=db.page_task(status)))


@api.route('/strategy/<int:strategy_id>', methods=["GET"])
def get_strategy_info(strategy_id):
    strategy_info = db.get_strategy_info(strategy_id)
    return jsonify(ResultResp().ok(data=strategy_info))


@api.route('/quota/<int:task_id>', methods=["GET"])
def get_user_quota_data(task_id):
    quota_data = CacheUtil().get(REALTIME_QUOTA % task_id)
    return jsonify(ResultResp().ok(data=quota_data))


@api.route('/user/<int:ue_id>/order/summary', methods=["GET"])
def get_user_order_summary(ue_id):
    strategy = request.args['strategy']
    order_summary = db.get_order_summary(ue_id, strategy)
    return jsonify(ResultResp().ok(data=order_summary))


@api.route('/user/<int:ue_id>/day_order/summary', methods=["GET"])
def get_day_order_summary(ue_id):
    strategy = request.args['strategy']
    day_order_summary = db.get_day_order_summary(ue_id, strategy)
    return jsonify(ResultResp().ok(data=day_order_summary))


@api.route('/user/<int:ue_id>/order', methods=["GET"])
def get_limit_order(ue_id):
    limit = request.args['limit']
    strategy = request.args['strategy']
    limit = limit if limit else 10

    day_order_summary = db.get_lastest_order(ue_id, strategy=strategy, limit=limit)
    return jsonify(ResultResp().ok(data=day_order_summary))


@api.route('/account/position', methods=["GET"])
def get_account_position():
    """
    获取仓位数据
    :return:
    """
    return jsonify(ResultResp().ok(data=BitMexRealTime().get_position(SymbolInfo('XBt', 'BTC', 'XBTUSD', 'BTC/USD'))))


@api.route('/account/wallet', methods=["GET"])
def get_account_wallet():
    """
    获取钱包数据
    :return:
    """
    return jsonify(ResultResp().ok(data=BitMexRealTime().get_wallet(SymbolInfo('XBt', 'BTC', 'XBTUSD', 'BTC/USD'))))


