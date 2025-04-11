import json
from typing import Any

import msgpack
import redis

from xyzs_py.XLogs import XLogs

logger = XLogs(__name__)


class XCache:
    def __init__(self, host='127.0.0.1', port=6379, username='', password='', db=0):
        """
        初始化XCache配置。

        :param host: Redis服务器地址
        :param port: Redis服务器端口
        :param username: Redis用户名（7.0及以上版本需要）
        :param password: Redis密码
        :param db: Redis数据库索引
        """
        self._host = host
        self._port = port
        self._username = username
        self._password = password
        self._db = db
        self._client = None  # 延迟初始化

    def _init_client(self):
        """
        初始化Redis客户端（延迟初始化）。
        """
        if self._client is None:
            try:
                self._client = redis.Redis(
                    host=self._host,
                    port=self._port,
                    db=self._db,
                    username=self._username,
                    password=self._password,
                    decode_responses=False  # 关闭解码，以便读取字节数据
                )
                # 测试连接
                self._client.ping()
                logger.info(f"Redis connect successful - {self._host}:{self._port}")
                return True  # 初始化成功
            except redis.ConnectionError as e:
                logger.error(f"redis connect failed - {self._host}:{self._port} "
                             f"username={self._username} "
                             f"password={self._password} "
                             f"db={self._db} "
                             f":{e}")
                return False  # 初始化失败
        return True  # 已经初始化

    def serialize(self, value: Any) -> bytes:
        # 如果是 SQLAlchemy 模型对象，转换为字典
        if hasattr(value, '__dict__'):
            # 过滤掉 SQLAlchemy 内部属性（如 '_sa_instance_state'）
            value_dict = {k: v for k, v in value.__dict__.items() if not k.startswith('_')}
            return msgpack.packb(value_dict)
        return msgpack.packb(value)

    def deserialize(self, value: bytes) -> Any:
        return msgpack.unpackb(value, raw=False)

    def set(self, key, value, expire=3600000):
        """
        设置缓存键值对。

        :param key: 缓存键
        :param value: 缓存值
        :param expire: 过期时间（毫秒），如果为None，则使用全局默认过期时间
        :return: 设置结果，成功返回True，否则返回None
        """
        try:
            if not self._init_client():
                logger.error("Redis客户端未初始化，无法设置键值")
                return False

            # 处理值的序列化
            serialize_value = self.serialize(value=value)
            return self._client.set(name=key, value=serialize_value, px=expire)
        except redis.RedisError as e:
            logger.error(f"设置[{key}]键值对失败: {e}")
            return False
        except Exception as e:
            logger.error(f"设置[{key}]键值对失败: {e}")

    def get(self, key, default=None, cls=None):
        """
        获取缓存值。
        :param key: 缓存键
        :param default: 默认值
        :param cls: 可选的类，用于将字典反序列化为对象实例
        :return: 缓存值，或default如果键不存在或发生错误
        """
        try:
            if not self._init_client():
                logger.error("Redis客户端未初始化，无法获取键值")
                return default

            value = self._client.get(name=key)
            if value is None:
                return default

            # 反序列化
            deserialized_value = self.deserialize(value)

            # 如果指定了 cls，则将字典转为对象
            if cls and isinstance(deserialized_value, dict):
                return cls(**deserialized_value)

            return deserialized_value

        except redis.RedisError as e:
            logger.error(f"获取键 {key} 的值失败: {e}")
            return default
        except Exception as e:
            logger.error(f"获取键 {key} 的值失败: {e}")
            return default

    def delete(self, key):
        """
        删除缓存键。

        :param key: 缓存键
        :return: 删除成功的键数量，或None如果发生错误
        """
        try:
            if not self._init_client():
                logger.error("Redis客户端未初始化，无法设置键值")
                return None

            return self._client.delete(key)
        except redis.RedisError as e:
            logger.error(f"删除键 {key} 失败: {e}")
            return 0

    def exists(self, key):
        """
        检查缓存键是否存在。

        :param key: 缓存键
        :return: 如果存在返回True，否则返回False
        """
        try:
            if not self._init_client():
                logger.error("Redis客户端未初始化，无法设置键值")
                return None

            return self._client.exists(key)
        except redis.RedisError as e:
            logger.error(f"检查键 {key} 是否存在失败: {e}")
            return False

    def increment(self, key, amount=1):
        """
        递增键的整数值。

        :param key: 缓存键
        :param amount: 递增量，默认为1
        :return: 递增后的新值，或None如果发生错误
        """
        try:
            if not self._init_client():
                logger.error("Redis客户端未初始化，无法设置键值")
                return None

            return self._client.incr(name=key, amount=amount)
        except redis.RedisError as e:
            logger.error(f"递增键 {key} 的值失败: {e}")
            return None

    def decrement(self, key, amount=1):
        """
        递减键的整数值。

        :param key: 缓存键
        :param amount: 递减量，默认为1
        :return: 递减后的新值，或None如果发生错误
        """
        try:
            if not self._init_client():
                logger.error("Redis客户端未初始化，无法设置键值")
                return None
            return self._client.decr(name=key, amount=amount)
        except redis.RedisError as e:
            logger.error(f"递减键 {key} 的值失败: {e}")
            return None

    def getStr(self, key, default=''):
        """获取字符串类型的值"""
        return str(self.get(key, default))

    def getInt(self, key, default=0):
        """获取整数类型的值"""
        try:
            return int(self.get(key, default))
        except ValueError:
            return default

    def getFloat(self, key, default=0.0):
        """获取浮点数类型的值"""
        try:
            return float(self.get(key, default))
        except ValueError:
            return default

    def getBool(self, key, default=False):
        """获取布尔类型的值"""
        value = self.get(key, default)
        if isinstance(value, str):
            return value.lower() in ['true', '1', 'yes']
        return bool(value)

    def getList(self, key, default=None):
        """获取列表类型的值"""
        value = self.get(key, default)
        if isinstance(value, str):
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return default
        return value if isinstance(value, list) else default

    def getDict(self, key, default=None):
        """获取字典类型的值"""
        value = self.get(key, default)
        if isinstance(value, str):
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return default
        return value if isinstance(value, dict) else default
