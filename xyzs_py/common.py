import hashlib
import uuid
from math import ceil

from xyzs_py.SyncResult import SyncResult


class common:

    @staticmethod
    def api_cb(code: int, msg: str = None, data=None):
        """
        API响应前端数据结构
        :param code: 响应代码，一般0为正常，1以上都是错误代码
        :param msg:  响应消息描述
        :param data: 响应数据
        :return:
        """
        if code == 1 and not msg:
            msg = "操作失败"

        response = {
            "code": code,
            "msg": msg,
        }
        if data:
            response["data"] = data
        return response

    @staticmethod
    def api_cb_page(code: int = 0, msg: str = '', count: int = 0, page: int = 1, limit: int = 1, data=None):
        """
        API 分页响应前端数据结构
        """
        if code == 1 and not msg:
            msg = "操作失败"

        pages = ceil(count / limit)  # 向上取整计算页数

        response = {
            "code": code,
            "msg": msg,
            "count": count,
            "page": page,
            "pages": pages
        }
        if data:
            response["data"] = data
        return response

    @staticmethod
    def api_cb_sync_result(r: SyncResult):
        """
        将SyncResult结果以结构化的API响应前端
        """
        return common.api_cb(r.code, msg=r.msg, data=r.data)

    @staticmethod
    def md5(text: str) -> str:
        hash_obj = hashlib.md5(text.encode('utf-8'))
        return hash_obj.hexdigest()

    @staticmethod
    def uuid() -> str:
        return str(uuid.uuid4())
