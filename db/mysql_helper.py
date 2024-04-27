from singleton_decorator import singleton

from db.mysql_pool import get_my_connection


@singleton
class MySqlHelper(object):

    _instance = None

    def __init__(self):
        self.db = get_my_connection()  # 从数据池中获取连接

    # 封装执行命令
    def execute(self, sql, param=None, auto_close=False):
        """
        【主要判断是否有参数和是否执行完就释放连接】
        :param sql: 字符串类型，sql语句
        :param param: sql语句中要替换的参数"select %s from tab where id=%s" 其中的%s就是参数
        :param auto_close: 是否关闭连接
        :return: 返回连接conn和游标cursor
        """
        cursor, conn = self.db.get_conn()  # 从连接池获取连接
        count = 0
        try:
            # count : 为改变的数据条数
            if param:
                count = cursor.execute(sql, param)
            else:
                count = cursor.execute(sql)
            conn.commit()
            if auto_close:
                self.close(cursor, conn)
        except Exception as e:
            raise e
        return cursor, conn, count

    # 执行多条命令
    # def executemany(self, lis):
    #     """
    #     :param lis: 是一个列表，里面放的是每个sql的字典'[{"sql":"xxx","param":"xx"}....]'
    #     :return:
    #     """
    #     cursor, conn = self.db.getconn()
    #     try:
    #         for order in lis:
    #             sql = order['sql']
    #             param = order['param']
    #             if param:
    #                 cursor.execute(sql, param)
    #             else:
    #                 cursor.execute(sql)
    #         conn.commit()
    #         self.close(cursor, conn)
    #         return True
    #     except Exception as e:
    #         print(e)
    #         conn.rollback()
    #         self.close(cursor, conn)
    #         return False

    # 释放连接
    def close(self, cursor, conn):
        """释放连接归还给连接池"""
        cursor.close()
        conn.close()

    # 查询所有
    def select_all(self, sql, param=None):
        try:
            cursor, conn, count = self.execute(sql, param)
            res = cursor.fetchall()
            return res
        except Exception as e:
            raise e
            return count

    # 查询单条
    def select_one(self, sql, param=None):
        try:
            cursor, conn, count = self.execute(sql, param)
            res = cursor.fetchone()
            return res
        except Exception as e:
            raise e
            return count

    # 增加
    def insert_one(self, sql, param):
        try:
            cursor, conn, count = self.execute(sql, param)
            __id = cursor.lastrowid  # 获取当前插入数据的主键id，该id应该为自动生成为好
            conn.commit()
            return __id
            # 防止表中没有id返回0
            # if _id == 0:
            #     return True
            # return _id
        except Exception as e:
            conn.rollback()
            raise e

    # 增加多行
    def insert_many(self, sql, param):
        """
        :param sql:
        :param param: 必须是元组或列表[(),()]或（（），（））
        :return:
        """
        cursor, conn = self.db.get_conn()
        try:
            cursor.executemany(sql, param)
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e

    # 删除
    def delete(self, sql, param=None):
        try:
            cursor, conn, count = self.execute(sql, param)
            return count
        except Exception as e:
            conn.rollback()
            raise e

    # 更新
    def update(self, sql, param=None):
        try:
            cursor, conn, count = self.execute(sql, param)
            conn.commit()
            return count
        except Exception as e:
            conn.rollback()
            raise e
