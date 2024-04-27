
import response.error_code as code


class ResultResp(object):

    def __init__(self):
        self.message = '操作成功'
        self.code = code.OK
        self.data = None

    def __struct(self):
        if self.data:
            return {
                'code': self.code,
                'message': self.message,
                'data': self.data
            }
        else:
            return {
                'code': self.code,
                'message': self.message
            }

    def ok(self, data=None, msg=None):
        self.code = code.OK
        if data:
            self.data = data

        if msg:
            self.message = msg

        return self.__struct()

    def failed(self, message):
        self.code = code.FAIL
        self.message = message
        return self.__struct()

    def failed(self, __code, message=None):
        self.code = __code
        self.message = '操作失败'

        if message:
            self.message = message

        return self.__struct()
