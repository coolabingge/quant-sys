import datetime

from loguru import logger

import constants.constant as const
import db.db_sql as db
from algorithm.quant_common import QuantCommon
from enums.used import Side, OrderType, OpenType, Env
from event.event_engine import Event
from exception.exception import QuantException
from model.params import OrderCreateParams, DbOrderInfo, OrderResp
from trade.base_trade import BaseTrade
from utils import base_utils
from utils.base_utils import decimal_fmt
from utils.cache_util import CacheUtil, REALTIME_QUOTA
from utils.id_util import IdWorker


class MACDFinishStrategy(object):
    """
    BBM策略执行器
    """
    def __init__(self, market_trade: BaseTrade, event: Event, user_id=None, task_config=None, env=Env.Dist, task_id=None):
        self.event = event
        self.user_id = user_id
        self.task_config = task_config
        self.env = env
        self.market_trade = market_trade
        self.task_id = task_id

        # 处理数据
        line_data = self.event.data
        self.exchange_name = self.event.exchange_name
        self.symbol_info = self.event.symbol_info
        # 获取分钟数曲线
        period_frame = base_utils.period_frame(line_data, self.task_config['orderPeriod'])
        # pprint(period_frame)

        self.leverage = self.task_config['multiply']

        recent_frame = period_frame.iloc[-1:]
        # 最进K线的收盘价即为当前价
        self.cur_price = recent_frame[const.CLOSE][-1]

        algorithm = QuantCommon(self.exchange_name)

        # 算法数据
        self.rst = algorithm.result(period_frame)
        self.current_line = str(period_frame.index[-1:][0]).strip("'")
        self.__handle_quota_data(self.rst)

        if not user_id:
            raise QuantException(message='执行策略需要用户ID')

    def check_period_finish(self, current_last_period):
        before_period_time = self.market_trade.get_last_finish_period()
        # logger.info("before_period_time: %s, current_last_period: %s" % (before_period_time, current_last_period))
        # 如果当前K线最后一个时间段和上一个时间段不等，则说明跨线了，此时会触发策略匹配
        if before_period_time and current_last_period and current_last_period != before_period_time:
            self.market_trade.set_last_finish_period(current_last_period)
            return True
        # 同一个时间段内的实时，不处理策略匹配
        self.market_trade.set_last_finish_period(current_last_period)
        return False

    def __handle_quota_data(self, rst=None):
        quota_data = {
            'current_line': self.current_line,
            'symbol_pair': self.event.symbol_info.symbol_pair,
            'price': decimal_fmt(self.cur_price, 4),
            'boll': {
                'upper': decimal_fmt(self.rst['BOLL_UPPER'], 3),
                'lower': decimal_fmt(self.rst['BOLL_LOWER'], 4)
            },
            'macd_base': {
                'value': decimal_fmt(self.rst['MACD'], 4),
                'value_before': decimal_fmt(self.rst['MACD_BEFORE'], 4),
                'dif': decimal_fmt(self.rst['MACD_DIFF'], 4),
                'dea': decimal_fmt(self.rst['MACD_DEA'], 3)
            },
            'macd_reverse': {
                'value': '--',
                'dif': '--',
                'dea': '--'
            },
            'bbi': decimal_fmt(self.rst['BBI'], 4)
        }
        self._add_runtime_quota(quota_data)
        return quota_data

    def _add_runtime_quota(self, quota_data=None):
        if not self.task_id:
            return
        CacheUtil().set(REALTIME_QUOTA % self.task_id, quota_data)

    # 策略执行开始
    def execute(self):
        # 开多开空判断
        macd = self.rst['MACD'] * 2
        macd_before = self.rst['MACD_BEFORE'] * 2
        macd_dif = float(self.rst['MACD_DIFF'])
        macd_dea = float(self.rst['MACD_DEA'])
        much = macd_dif > 0 and macd_dea > 0
        less = (macd_dif < 0) and (macd_dea < 0)

        self.stop_win_check()
        if not self.check_period_finish(self.current_line):
            return

        logger.info("[%s]进入策略，当前Line线: %s, 当前参数: macd上穿, 当前价格：%s, 倍数: %s, macd: %s, macd_before: %s, macd_dif: %s, macd_dea: %s" % (
            self.symbol_info.symbol_pair_ccxt, self.current_line, self.cur_price, self.leverage, macd, macd_before, macd_dif, macd_dea))
        # logger.info("非实时状态下触发点位，时间：%s,柱状区间：%s,")

        # macd向上形成交叉
        if macd > 0 and macd_before < 0 and much:
            last_trade_interval = self.market_trade.last_trade_interval(self.user_id, self.symbol_info)
            # 单次成功交易间隔3分钟
            if last_trade_interval and (last_trade_interval <= 3 * 60):
                return

            logger.info("[%s]macd上穿, 开单价格：%s, 倍数: %s, macd: %s, macd_before: %s, macd_dif: %s, macd_dea: %s" % (
                self.symbol_info.symbol_pair_ccxt, self.cur_price, self.leverage, macd, macd_before, macd_dif, macd_dea))
            self.open_stock(self.cur_price, Side.Open_More)
        elif macd < 0 and macd_before > 0 and less:
            last_trade_interval = self.market_trade.last_trade_interval(self.user_id, self.symbol_info)
            # 单次成功交易间隔3分钟
            if last_trade_interval and (last_trade_interval <= 3 * 60):
                return

            logger.info("[%s]macd下穿, 开单价格：%s, 倍数: %s, macd: %s, macd_before: %s, macd_dif: %s, macd_dea: %s" % (
                self.symbol_info.symbol_pair_ccxt, self.cur_price, self.leverage, macd, macd_before, macd_dif, macd_dea))
            self.open_stock(self.cur_price, Side.Open_Empty)

    def get_percent_before_price(self, open_price=None, percent=None, before_level_percent=None, direction=None):
        open_price = float(open_price)
        percent = float(percent)
        before_level_percent = float(before_level_percent)

        if direction == 'long':
            long_before_percent_price = open_price/(1 - (percent - before_level_percent)/self.leverage)
            return long_before_percent_price
        elif direction == 'short':
            short_before_percent_price = open_price/((percent - before_level_percent)/self.leverage + 1)
            return short_before_percent_price

    # 止盈检查
    def stop_win_check(self):
        # 获取当前实时仓位数据
        positions = self.market_trade.get_position(self.symbol_info)

        if not positions and (len(positions) == 0):
            return

        for position in positions:
            open_price = position.buy_price
            # < 0 当前仓位是开空的，>0当前仓位是开多的仓位
            stock_qty = position.current_qty

            # 赢率超过当前配置，平仓 | 当前价超过布林上轨
            stop_win_rate = self.task_config['stopWinRate'] / 100
            # 获取缓存是否有上调的止赢率
            cache_win_rate = self.market_trade.get_win_rate(self.user_id, self.symbol_info, position.direction)
            stop_win_rate = stop_win_rate if not cache_win_rate else cache_win_rate
            # 止损率
            stop_lose_rate = self.task_config['stopLoseRate'] / 100
            win_rate = self.get_win_lose_rate(open_price, self.cur_price, stock_qty, position.direction)

            # 赢率
            win_rate_ok = (win_rate > 0) and (win_rate >= stop_win_rate)
            # 损率
            lose_rate_ok = (win_rate < 0) and ((abs(win_rate)) >= stop_lose_rate)

            if lose_rate_ok:
                logger.info("[%s]策略：3，环境:%s, 用户：%s，当前仓位赢率：%s，量: %s, 达到损率条件, 平仓" % (self.symbol_info.symbol_pair_ccxt, self.env, self.user_id, win_rate, stock_qty))
                self.empty_stock(stock_qty, win_rate, position.direction)
                continue

            level_percent = self.task_config['increatementWinRate']/100 or 0.05
            # 获取当前止损价格
            lose_price = self.market_trade.get_lose_price(user_id=self.user_id,
                                                          symbol_info=self.symbol_info,
                                                          direction=position.direction)

            if win_rate != 0:
                logger.info("[%s]策略：3，环境:%s, 用户：%s，仓位盈亏率: %s, 当前被动赢亏止损价：%s, 方向: %s" % (self.symbol_info.symbol_pair_ccxt, self.env.name, self.user_id, win_rate, lose_price, position.direction))

            # 满足止赢率
            if win_rate_ok:
                lose_price = self.get_percent_before_price(open_price=open_price,
                                                           percent=win_rate,
                                                           direction=position.direction,
                                                           before_level_percent=level_percent)
                logger.info("方向：%s, 超过赢率: %s, 设置[%s]止损价: %s, 上调止盈率至: %s" % (
                    position.direction, win_rate, (win_rate - level_percent), lose_price,
                    (stop_win_rate + level_percent)))

                self.market_trade.set_lose_price(user_id=self.user_id,
                                                 symbol_info=self.symbol_info,
                                                 price=lose_price,
                                                 direction=position.direction)
                self.market_trade.set_win_rate(user_id=self.user_id,
                                               symbol_info=self.symbol_info,
                                               direction=position.direction,
                                               rate=(stop_win_rate + level_percent))

            # 被动止损触发位置程序
            if lose_price and (float(self.cur_price) <= lose_price) and (position.direction == 'long'):
                logger.info("[%s]策略：3， 环境：%s, 用户：%s, 方向：多, 被动止损触发金额: %s, 量：%s, 平仓" % (self.symbol_info.symbol_pair_ccxt, self.env.name, self.user_id, lose_price, stock_qty))
                self.empty_stock(stock_qty, win_rate, position.direction)
                self.market_trade.set_lose_price(user_id=self.user_id,
                                                 symbol_info=self.symbol_info,
                                                 price=None,
                                                 direction=position.direction)
                self.market_trade.set_win_rate(user_id=self.user_id,
                                               symbol_info=self.symbol_info,
                                               direction=position.direction,
                                               rate=None)
            elif lose_price and (float(self.cur_price >= lose_price)) and (position.direction == 'short'):
                logger.info("[%s]策略：3， 环境：%s, 用户：%s, 方向：空, 被动止损触发金额: %s, 量：%s, 平仓" % (self.symbol_info.symbol_pair_ccxt, self.env.name, self.user_id, lose_price, stock_qty))
                self.empty_stock(stock_qty, win_rate, position.direction)
                self.market_trade.set_lose_price(user_id=self.user_id,
                                                 symbol_info=self.symbol_info,
                                                 price=None,
                                                 direction=position.direction)
                self.market_trade.set_win_rate(user_id=self.user_id,
                                               symbol_info=self.symbol_info,
                                               direction=position.direction,
                                               rate=None)

    """
    计算开多？空下的赢亏率
    """
    def get_win_lose_rate(self, open_price, cur_price, qty, position_type):
        cur_price = float(cur_price)
        open_price = float(open_price)
        if float(qty) < 0:
            position_type = 'short'

        # 空仓
        if (open_price == 0) or (float(qty) == 0):
            return 0

        # 开多赢亏率计算
        if position_type == 'long':
            # 赢
            if cur_price >= open_price:
                win_rate = (1 - open_price / cur_price) * self.leverage
            else:
                # 亏
                win_rate = -((1 - cur_price / open_price) * self.leverage)
        else:
            # 开空盈亏率
            # 赢, 少出来的算赚
            if cur_price <= open_price:
                win_rate = (open_price / cur_price - 1) * self.leverage
            else:
                # 亏, 多出来的算亏
                win_rate = -((cur_price / open_price - 1) * self.leverage)

        return win_rate

    # 开仓
    def open_stock(self, buy_price, side: Side = None):
        buy_price = decimal_fmt(buy_price, 1)
        logger.info('开仓，%s开仓价格：%s' % (self.symbol_info.symbol_pair, buy_price))

        # 每单下单量,任务配置获取
        every_qty = self.task_config['orderMoney']
        wallet = self.market_trade.get_wallet(self.symbol_info)

        # 持仓率计算，通过钱包的使用率计算持仓
        stock_rate = wallet.position_rate
        logger.info("当前持有仓位: %s, 总仓位%s: %s, 持仓率: %s" % (wallet.used, self.symbol_info.symbol_pair, wallet.amount, wallet.position_rate))
        # 最大配置持仓率
        max_stock_rate = self.task_config['maxStockRate']/100
        if stock_rate >= max_stock_rate:
            cancel_orders = self.market_trade.cancel_all_buy_orders(self.symbol_info)
            db.cancel_orders(cancel_orders)
            logger.info('持仓比超过配置，不开单并取消当前所有委托单, 撤单数: %d, 持仓比: %s' % (len(cancel_orders), str(stock_rate)))
            return

        order_create_params = OrderCreateParams(
            client_oid="%s%d%s" % (self.exchange_name, self.task_id, IdWorker().get_id()),
            side=side,
            order_type=OrderType.Market,
            price=buy_price,
            order_qty=every_qty,
            win_rate=0,
            status='open'
        )

        # okex创建合约订单开仓
        self.market_trade.create_order(order_create_params, self.symbol_info, leverage=self.leverage)
        # 记录交易时间戳，计算交易间隔
        self.market_trade.set_last_trade_time(user_id=self.user_id, symbol_info=self.symbol_info)

    # 平仓
    def empty_stock(self, stock_qty, win_rate, position_type=None):
        if stock_qty == 0:
            return

        self.market_trade.close_position(self.symbol_info, position_type=position_type)

    def record_order(self, params: OrderCreateParams, remote_order: OrderResp = None):
        try:
            profit_price = params.win_rate * params.order_qty
            price = remote_order[0]['price']
            db.insert_order(DbOrderInfo(
                exchange=self.exchange_name,
                symbol_info=self.symbol_info,
                order_price=decimal_fmt(price, 4),
                order_usdt=decimal_fmt(params.order_qty, 4),
                other_money=0,
                exchange_order_id=remote_order.order_id,
                exchange_order_time=datetime.datetime.now(),
                side=params.side,
                order_type=params.order_type,
                status=params.status,
                open_type=OpenType.Much if params.order_qty > 0 else OpenType.Less,
                sell_price=decimal_fmt(price, 4),
                profit_rate=decimal_fmt(params.win_rate, 4),
                profit_price=decimal_fmt(profit_price, 4),
            ))
        except Exception as e:
            raise e
