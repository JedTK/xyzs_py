import redis
from threading import Lock

from xyzs_py.XLogs import XLogs

log = XLogs()


class XCache:
    """
    XCache类用于管理Redis缓存，支持单例模式确保全局唯一实例。

    该类提供了对Redis的基本操作，包括设置、获取、删除键值对，检查键是否存在，
    以及递增和递减键的值。支持Redis 7.0及以上版本的身份验证，能够设置全局默认
    过期时间和键前缀。
    """
    _instance = None
    _lock = Lock()

    def __new__(cls, *args, **kwargs):
        """
        单例模式实现，确保类在全局范围内只有一个实例。
        """
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = super(XCache, cls).__new__(cls)
        return cls._instance

    def __init__(self, host='localhost', port=6379, username=None, password=None, db=0, expire=3600, prefix=''):
        """
        初始化XCache实例，连接到Redis服务器。

        :param host: Redis服务器地址
        :param port: Redis服务器端口
        :param username: Redis用户名（7.0及以上版本需要）
        :param password: Redis密码
        :param db: Redis数据库索引
        :param expire: 默认全局过期时间（毫秒）
        :param prefix: 键前缀
        """
        if not hasattr(self, 'client'):
            try:
                # 初始化Redis连接
                self.client = redis.Redis(
                    host=host,
                    port=port,
                    db=db,
                    username=username,
                    password=password,
                    decode_responses=True  # 自动解码返回的字节串为字符串
                )
                # 测试连接
                self.client.ping()

                # 存储配置
                self.expire = expire
                self.prefix = prefix

            except redis.ConnectionError as e:
                log.error(f"无法连接到Redis: {e}")
                raise e

    @classmethod
    def initialize(cls, host='localhost', port=6379, username=None, password=None, db=0, expire=3600, prefix=''):
        """
        初始化Redis连接，全局唯一实例

        :param host: Redis服务器地址
        :param port: Redis服务器端口
        :param db: Redis数据库索引
        :param username: Redis用户名（7.0及以上版本需要）
        :param password: Redis密码
        :param expire: 默认全局过期时间（毫秒）
        :param prefix: 键前缀
        """
        if cls._instance is None:
            cls._instance = cls(host, port, username, password, db, expire, prefix)
            log.info("XCache已初始化")

    @staticmethod
    def set(key, value, expire=None):
        """
        设置缓存键值对。

        :param key: 缓存键
        :param value: 缓存值
        :param expire: 过期时间（毫秒），如果为None，则使用全局默认过期时间
        :return: 设置结果，成功返回True，否则返回None
        """
        if not XCache._instance:
            log.error("缓存没有初始化，请先在程序入口进行初始化")
            return None

        try:
            # 添加键前缀
            key = f"{XCache._instance.prefix}{key}"
            # 使用指定的过期时间或默认全局过期时间
            expire = expire if expire is not None else XCache._instance.expire
            return XCache._instance.client.set(name=key, value=value, px=expire)
        except redis.RedisError as e:
            log.error(f"设置[{key}]键值对失败: {e}")
            return None

    @staticmethod
    def get(key, default=None):
        """
        获取缓存值。
        :param key: 缓存键
        :param default: 默认值
        :return: 缓存值，或None如果键不存在或发生错误
        """
        if not XCache._instance:
            log.error("缓存没有初始化，请先在程序入口进行初始化")
            return None

        try:
            # 添加键前缀
            key = f"{XCache._instance.prefix}{key}"
            value = XCache._instance.client.get(name=key)
            if not value:
                return default
            return value
        except redis.RedisError as e:
            log.error(f"获取键 {key} 的值失败: {e}")
            return None

    @staticmethod
    def delete(key):
        """
        删除缓存键。

        :param key: 缓存键
        :return: 删除成功的键数量，或None如果发生错误
        """
        if not XCache._instance:
            log.error("缓存没有初始化，请先在程序入口进行初始化")
            return None

        try:
            # 添加键前缀
            key = f"{XCache._instance.prefix}{key}"
            return XCache._instance.client.delete(key)
        except redis.RedisError as e:
            log.error(f"删除键 {key} 失败: {e}")
            return None

    @staticmethod
    def exists(key):
        """
        检查缓存键是否存在。

        :param key: 缓存键
        :return: 如果存在返回True，否则返回False
        """
        if not XCache._instance:
            log.error("缓存没有初始化，请先在程序入口进行初始化")
            return False

        try:
            # 添加键前缀
            key = f"{XCache._instance.prefix}{key}"
            return XCache._instance.client.exists(key)
        except redis.RedisError as e:
            log.error(f"检查键 {key} 是否存在失败: {e}")
            return False

    @staticmethod
    def increment(key, amount=1):
        """
        递增键的整数值。

        :param key: 缓存键
        :param amount: 递增量，默认为1
        :return: 递增后的新值，或None如果发生错误
        """
        if not XCache._instance:
            log.error("缓存没有初始化，请先在程序入口进行初始化")
            return None

        try:
            # 添加键前缀
            key = f"{XCache._instance.prefix}{key}"
            return XCache._instance.client.incr(name=key, amount=amount)
        except redis.RedisError as e:
            log.error(f"递增键 {key} 的值失败: {e}")
            return None

    @staticmethod
    def decrement(key, amount=1):
        """
        递减键的整数值。

        :param key: 缓存键
        :param amount: 递减量，默认为1
        :return: 递减后的新值，或None如果发生错误
        """
        if not XCache._instance:
            log.error("缓存没有初始化，请先在程序入口进行初始化")
            return None

        try:
            # 添加键前缀
            key = f"{XCache._instance.prefix}{key}"
            return XCache._instance.client.decr(name=key, amount=amount)
        except redis.RedisError as e:
            log.error(f"递减键 {key} 的值失败: {e}")
            return None

    @staticmethod
    def getStr(key, default=''):
        """获取字符串类型的值"""
        return str(XCache.get(key, default))

    @staticmethod
    def getInt(key, default=0):
        """获取整数类型的值"""
        try:
            return int(XCache.get(key, default))
        except ValueError:
            return default

    @staticmethod
    def getFloat(key, default=0.0):
        """获取浮点数类型的值"""
        try:
            return float(XCache.get(key, default))
        except ValueError:
            return default

    @staticmethod
    def getBool(key, default=False):
        """获取布尔类型的值"""
        value = XCache.get(key, default)
        if isinstance(value, str):
            return value.lower() in ['true', '1', 'yes']
        return bool(value)

    @staticmethod
    def getList(key, default=None):
        """获取列表类型的值"""
        value = XCache.get(key, default)
        if isinstance(value, list):
            return value
        try:
            return eval(value) if isinstance(value, str) else default
        except Exception:
            return default

    @staticmethod
    def getDict(key, default=None):
        """获取字典类型的值"""
        value = XCache.get(key, default)
        if isinstance(value, dict):
            return value
        try:
            return eval(value) if isinstance(value, str) else default
        except Exception:
            return default
