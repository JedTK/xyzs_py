import json
from datetime import datetime, date
from decimal import Decimal
from enum import Enum
from typing import Any, get_origin, get_args

import msgpack
import redis

from xyzs_py.XLogs import XLogs

logger = XLogs(__name__)

_TYPE_KEY = "__xyzs_py_xcache_type__"
_VALUE_KEY = "__xyzs_py_xcache_value__"

_TYPE_DECIMAL = "decimal"
_TYPE_DATETIME = "datetime"
_TYPE_DATE = "date"


class XCache:
    def __init__(self, host="127.0.0.1", port=6379, username="", password="", db=0):
        """
        初始化 XCache 配置。

        :param host: Redis 服务器地址
        :param port: Redis 服务器端口
        :param username: Redis 用户名
        :param password: Redis 密码
        :param db: Redis 数据库索引
        """
        self._host = host
        self._port = port
        self._username = username
        self._password = password
        self._db = db
        self._client = None

    def _init_client(self) -> bool:
        """
        初始化 Redis 客户端，延迟初始化。
        """
        if self._client is not None:
            return True

        try:
            kwargs = {
                "host": self._host,
                "port": self._port,
                "db": self._db,
                "decode_responses": False,
            }

            if self._username:
                kwargs["username"] = self._username

            if self._password:
                kwargs["password"] = self._password

            self._client = redis.Redis(**kwargs)
            self._client.ping()

            logger.info(f"Redis connect successful - {self._host}:{self._port}")
            return True

        except redis.ConnectionError as e:
            logger.error(
                f"redis connect failed - {self._host}:{self._port} "
                f"username={self._username} "
                f"password={self._mask_password(self._password)} "
                f"db={self._db} "
                f": {e}"
            )
            self._client = None
            return False

        except redis.RedisError as e:
            logger.error(
                f"redis init failed - {self._host}:{self._port} "
                f"username={self._username} "
                f"password={self._mask_password(self._password)} "
                f"db={self._db} "
                f": {e}"
            )
            self._client = None
            return False

    def serialize(self, value: Any) -> bytes:
        """
        序列化缓存数据。
        """
        try:
            cache_data = self._to_cache_data(value)
            return msgpack.packb(cache_data, use_bin_type=True)
        except Exception as e:
            logger.error(f"缓存序列化失败，value_type={type(value).__name__}: {e}")
            raise

    def deserialize(self, value: bytes) -> Any:
        """
        反序列化缓存数据，并恢复 Decimal / datetime / date 等特殊类型。
        """
        try:
            data = msgpack.unpackb(value, raw=False)
            return self._from_cache_data(data)
        except Exception as e:
            logger.error(f"缓存反序列化失败: {e}")
            raise

    def set(self, key, value, expire=3600000):
        """
        设置缓存键值对。

        :param key: 缓存键
        :param value: 缓存值
        :param expire: 过期时间，单位毫秒。如果为 None，则不过期。
        :return: 成功返回 True，失败返回 False
        """
        try:
            if not self._init_client():
                logger.error("Redis 客户端未初始化，无法设置键值")
                return False

            serialize_value = self.serialize(value=value)

            if expire is None:
                return bool(self._client.set(name=key, value=serialize_value))

            return bool(self._client.set(name=key, value=serialize_value, px=expire))

        except redis.RedisError as e:
            logger.error(f"设置[{key}]键值对失败: {e}")
            return False

        except Exception as e:
            logger.error(f"设置[{key}]键值对失败: {e}")
            return False

    def get(self, key, default=None, cls=None):
        """
        获取缓存值。

        :param key: 缓存键
        :param default: 默认值
        :param cls: 可选类型。
                    支持：
                    - SomeClass
                    - list[SomeClass]
                    - List[SomeClass]
        :return: 缓存值，或 default
        """
        try:
            if not self._init_client():
                logger.error("Redis 客户端未初始化，无法获取键值")
                return default

            value = self._client.get(name=key)
            if value is None:
                return default

            deserialized_value = self.deserialize(value)

            if cls is None:
                return deserialized_value

            if self._is_list_type(cls):
                item_cls = self._get_list_item_type(cls)

                if item_cls is None:
                    return deserialized_value

                if not isinstance(deserialized_value, list):
                    return default

                return [
                    self._dict_to_obj(item_cls, item)
                    if isinstance(item, dict)
                    else item
                    for item in deserialized_value
                ]

            if isinstance(deserialized_value, dict):
                return self._dict_to_obj(cls, deserialized_value)

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
        :return: 删除成功的键数量，失败返回 0
        """
        try:
            if not self._init_client():
                logger.error("Redis 客户端未初始化，无法删除键")
                return 0

            return self._client.delete(key)

        except redis.RedisError as e:
            logger.error(f"删除键 {key} 失败: {e}")
            return 0

    def exists(self, key) -> bool:
        """
        检查缓存键是否存在。

        :param key: 缓存键
        :return: 存在返回 True，否则返回 False
        """
        try:
            if not self._init_client():
                logger.error("Redis 客户端未初始化，无法检查键")
                return False

            return bool(self._client.exists(key))

        except redis.RedisError as e:
            logger.error(f"检查键 {key} 是否存在失败: {e}")
            return False

    def increment(self, key, amount=1):
        """
        递增键的整数值。

        :param key: 缓存键
        :param amount: 递增量
        :return: 递增后的新值，失败返回 None
        """
        try:
            if not self._init_client():
                logger.error("Redis 客户端未初始化，无法递增键")
                return None

            return self._client.incr(name=key, amount=amount)

        except redis.RedisError as e:
            logger.error(f"递增键 {key} 的值失败: {e}")
            return None

    def decrement(self, key, amount=1):
        """
        递减键的整数值。

        :param key: 缓存键
        :param amount: 递减量
        :return: 递减后的新值，失败返回 None
        """
        try:
            if not self._init_client():
                logger.error("Redis 客户端未初始化，无法递减键")
                return None

            return self._client.decr(name=key, amount=amount)

        except redis.RedisError as e:
            logger.error(f"递减键 {key} 的值失败: {e}")
            return None

    def getStr(self, key, default=""):
        """
        获取字符串类型的值。
        """
        value = self.get(key, default)
        if value is None:
            return default
        return str(value)

    def getInt(self, key, default=0):
        """
        获取整数类型的值。
        """
        try:
            return int(self.get(key, default))
        except (ValueError, TypeError):
            return default

    def getFloat(self, key, default=0.0):
        """
        获取浮点数类型的值。
        """
        try:
            return float(self.get(key, default))
        except (ValueError, TypeError):
            return default

    def getBool(self, key, default=False):
        """
        获取布尔类型的值。
        """
        value = self.get(key, default)

        if isinstance(value, bool):
            return value

        if isinstance(value, str):
            return value.strip().lower() in ["true", "1", "yes", "y", "on"]

        return bool(value)

    def getList(self, key, default=None):
        """
        获取列表类型的值。
        """
        value = self.get(key, default)

        if isinstance(value, list):
            return value

        if isinstance(value, str):
            try:
                parsed = json.loads(value)
                return parsed if isinstance(parsed, list) else default
            except json.JSONDecodeError:
                return default

        return default

    def getDict(self, key, default=None):
        """
        获取字典类型的值。
        """
        value = self.get(key, default)

        if isinstance(value, dict):
            return value

        if isinstance(value, str):
            try:
                parsed = json.loads(value)
                return parsed if isinstance(parsed, dict) else default
            except json.JSONDecodeError:
                return default

        return default

    def _to_cache_data(self, value: Any) -> Any:
        """
        将任意对象递归转换为 msgpack 可序列化的数据。
        同时对 Decimal / datetime / date 做类型标记，方便反序列化恢复类型。
        """
        if value is None:
            return None

        if isinstance(value, (str, int, float, bool, bytes)):
            return value

        if isinstance(value, Decimal):
            return {
                _TYPE_KEY: _TYPE_DECIMAL,
                _VALUE_KEY: str(value),
            }

        if isinstance(value, datetime):
            return {
                _TYPE_KEY: _TYPE_DATETIME,
                _VALUE_KEY: value.isoformat(),
            }

        if isinstance(value, date):
            return {
                _TYPE_KEY: _TYPE_DATE,
                _VALUE_KEY: value.isoformat(),
            }

        if isinstance(value, Enum):
            return value.value

        if isinstance(value, dict):
            return {
                str(k): self._to_cache_data(v)
                for k, v in value.items()
            }

        if isinstance(value, (list, tuple, set)):
            return [
                self._to_cache_data(item)
                for item in value
            ]

        if hasattr(value, "model_dump") and callable(value.model_dump):
            return self._to_cache_data(value.model_dump())

        if hasattr(value, "dict") and callable(value.dict):
            return self._to_cache_data(value.dict())

        if hasattr(value, "__dict__"):
            return {
                k: self._to_cache_data(v)
                for k, v in value.__dict__.items()
                if not k.startswith("_")
            }

        raise TypeError(f"无法缓存该对象类型: {type(value).__name__}")

    def _from_cache_data(self, value: Any) -> Any:
        """
        将 msgpack 反序列化后的数据递归恢复为 Python 对象。
        主要用于恢复 Decimal / datetime / date。
        """
        if value is None:
            return None

        if isinstance(value, (str, int, float, bool, bytes)):
            return value

        if isinstance(value, list):
            return [
                self._from_cache_data(item)
                for item in value
            ]

        if isinstance(value, dict):
            cache_type = value.get(_TYPE_KEY)

            if cache_type == _TYPE_DECIMAL:
                return Decimal(value[_VALUE_KEY])

            if cache_type == _TYPE_DATETIME:
                return datetime.fromisoformat(value[_VALUE_KEY])

            if cache_type == _TYPE_DATE:
                return date.fromisoformat(value[_VALUE_KEY])

            return {
                k: self._from_cache_data(v)
                for k, v in value.items()
            }

        return value

    def _dict_to_obj(self, cls: type, data: dict):
        """
        将 dict 转成指定对象。
        支持 Pydantic v2 / Pydantic v1 / 普通类 / SQLAlchemy Entity。
        """
        if hasattr(cls, "model_validate") and callable(cls.model_validate):
            return cls.model_validate(data)

        if hasattr(cls, "parse_obj") and callable(cls.parse_obj):
            return cls.parse_obj(data)

        return cls(**data)

    def _is_list_type(self, cls: Any) -> bool:
        """
        判断 cls 是否是 list[T] 或 List[T]。
        """
        origin = get_origin(cls)
        return origin is list

    def _get_list_item_type(self, cls: Any):
        """
        获取 list[T] 中的 T。
        """
        args = get_args(cls)

        if not args:
            return None

        return args[0]

    @staticmethod
    def _mask_password(password: str) -> str:
        """
        日志中隐藏 Redis 密码。
        """
        if not password:
            return ""

        if len(password) <= 2:
            return "**"

        return password[0] + "***" + password[-1]
