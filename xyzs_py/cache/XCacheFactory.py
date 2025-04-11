import os

from xyzs_py.XLogs import XLogs
from xyzs_py.cache.XCache import XCache

logger = XLogs(__name__)


class XCacheFactory:
    """
    XCache工厂类，支持管理多个XCache实例。
    """
    _instances = {}  # 用于存储已创建的XCache实例

    @classmethod
    def create(cls, name="default", host='127.0.0.1', port=6379, username='', password='', db=0):
        """
        创建一个新的XCache实例，如果已存在同名实例则返回现有实例。

        :param name: 实例名称（唯一标识）
        :param host: Redis服务器地址
        :param port: Redis服务器端口
        :param username: Redis用户名（7.0及以上版本需要）
        :param password: Redis密码
        :param db: Redis数据库索引
        :return: 新创建的XCache实例或现有实例
        """
        if name in cls._instances:
            # logger.warn(f"XCache实例 '{name}' 已存在，返回现有实例")
            return cls._instances[name]

        instance = XCache(host, port, username, password, db)
        cls._instances[name] = instance
        logger.info(f"XCache实例 '{name}' 创建成功")
        return instance

    @classmethod
    def get_default(cls, name="default"):
        return cls.get(name)

    @classmethod
    def get(cls, name="default"):
        """
        获取一个已有的XCache实例。

        :param name: 实例名称
        :return: XCache实例
        """
        if name not in cls._instances:
            # 不存在实列并且name还是default的话直接创建
            if name == "default":
                # 创建缓存工厂实例
                return XCacheFactory.create(host=os.getenv("redis.host", "127.0.0.1"),
                                            port=os.getenv("redis.port", 6379),
                                            username=os.getenv("redis.username", ""),
                                            password=os.getenv("redis.password", ""),
                                            db=os.getenv("redis.db", 0))
            else:
                logger.error(f"XCache实例 '{name}' 不存在，请先调用create方法创建")
                raise ValueError(f"XCache实例 '{name}' 不存在")
        return cls._instances[name]

    @classmethod
    def delete(cls, name="default"):
        """
        删除一个XCache实例。

        :param name: 实例名称
        """
        if name in cls._instances:
            del cls._instances[name]
            logger.info(f"XCache实例 '{name}' 已删除")
        else:
            logger.warn(f"尝试删除不存在的XCache实例 '{name}'")
