import time
import json


class SyncResult:
    def __init__(self, code=1, msg='', data=None):
        """
        初始化同步结果对象

        :param code: 响应代码
        :param msg: 错误消息
        :param data: API回调的主数据
        """
        self.code = code
        self.msg = msg
        self.data = data if data is not None else []
        self.create_time = int(time.time() * 1000)

    def set_data(self, data):
        """设置回调的数据"""
        self.data = data

    def set(self, code=1, msg='', data=None):
        """设置对应的结果"""
        self.code = code
        self.msg = msg
        self.data = data if data is not None else []
        self.create_time = int(time.time() * 1000)
        return self

    def set_error(self, code=1, msg='未知错误'):
        """设置对应的错误"""
        return self.set(code=code, msg=msg)

    def set_success(self, msg='', data=None):
        """设置对应的成功结果集合"""
        return self.set(code=0, msg=msg, data=data)

    def to_json_str(self):
        """转成json字符串"""
        return json.dumps(self.__dict__, ensure_ascii=False)
