

class QuantConfig(object):

    def __init__(self):
        self.id = None
        self.exchange = None


# print(0.00016 * 11302)
# print(0.000324 * 11467 - 1)

#
# def get_win_rate(open_price, cur_price, multiply):
#     # 未实现盈利 - 本金
#     win_rate = (1 - open_price/cur_price) * multiply
#     return win_rate
#
# print(get_win_rate(0.0324, 11466.72))
#
# # 100 11095 11466.03  161.99%
#
# # 盈利XBT ((1/11095) * 100 -  (1/11466.03) * 100) / (1/11095) * 100
# # 单XBT价格
#
# 11466.03 - 11095/ 11095
