from __future__ import annotations

from dataclasses import dataclass
from threading import RLock
from typing import Dict, Optional, Iterable, Callable

from xyzs_py.database import XDBConnect
from xyzs_py.database.XAsyncDBConnect import XAsyncDBConnect
from xyzs_py.database.XAsyncDBManager import XAsyncDBManager
from xyzs_py.database.XDBManager import XDBManager


@dataclass
class DBBundle:
    """将同一业务 key 下的同步/异步 DB 管理器打包管理。"""
    sync: Optional[XDBManager] = None
    async_: Optional[XAsyncDBManager] = None  # 避免与关键字冲突

    def ensure_any(self) -> "DBBundle":
        if self.sync is None and self.async_ is None:
            raise ValueError("DBBundle 为空：同步和异步管理器均为无。")
        return self


class XDBFactory:
    """
    数据库工厂
    - 以业务 key 为单位存放一组连接（同步/异步）
    - 支持仅注册同步、仅注册异步，或两者皆注册
    - 线程安全
    """

    _bundles: Dict[str, DBBundle] = {}
    _lock = RLock()

    __register_main_db_Listener = None
    __register_slave_DB_Listener = None

    __MAIN_DB_KEY = "main"

    @classmethod
    def register_main_db(cls, register_main_db_Listener):
        """
        注入主库注册监听器，允许调用者自主管理主库连接信息的注册。
        通常在应用启动时注入但不激活，待实际需要数据库连接时才触发注册。
        :param register_main_db_Listener: 主库监听器
        """
        cls.__register_main_db_Listener = register_main_db_Listener

    @classmethod
    def register_slave_db(cls, register_slave_DB_Listener):
        """
        注入注册从库监听器，允许调用者自主管理主库连接信息的注册。
        通常在应用启动时注入但不激活，待实际需要数据库连接时才触发注册。
        :param register_slave_DB_Listener: 从库监听器
        """
        cls.__register_slave_DB_Listener = register_slave_DB_Listener

    @classmethod
    def register(cls,
                 db_name: str = __MAIN_DB_KEY,
                 write_connect: Optional[XDBConnect] = None,
                 read_connect: Optional[XDBConnect] = None,
                 write_async_connect: Optional[XAsyncDBConnect] = None,
                 read_async_connect: Optional[XAsyncDBConnect] = None,
                 overwrite: bool = False) -> None:
        """
        注册数据库连接，支持同步/异步配置，以业务 key 分组存储。
        - 可只传同步（write_connect+read_connect）
        - 可只传异步（write_async_connect+read_async_connect）
        - 也可两者都传
        overwrite=True：重复注册会覆盖对应部分；False：若已存在则直接返回不进行覆盖
        """
        if not any([write_connect and read_connect, write_async_connect and read_async_connect]):
            raise ValueError("register 需要同时提供同步写/读 或 异步写/读 中的至少一组。")

        with cls._lock:
            bundle = cls._bundles.get(db_name, DBBundle())

            # 同步
            if write_connect is not None or read_connect is not None:
                if not (write_connect and read_connect):
                    raise ValueError("同步注册需要同时提供 write_connect 和 read_connect。")
                if bundle.sync is not None and not overwrite:
                    return
                bundle.sync = XDBManager(write_connect=write_connect, read_connect=read_connect)

            # 异步
            if write_async_connect is not None or read_async_connect is not None:
                if not (write_async_connect and read_async_connect):
                    raise ValueError("异步注册需要同时提供 write_async_connect 和 read_async_connect。")
                if bundle.async_ is not None and not overwrite:
                    return
                bundle.async_ = XAsyncDBManager(write_connect=write_async_connect,
                                                read_connect=read_async_connect)
            cls._bundles[db_name] = bundle.ensure_any()

    # region remark - 获取同步 DB 管理器

    @classmethod
    def get_sync_db(cls, db_name: str = __MAIN_DB_KEY, *, required: bool = True) -> Optional[XDBManager]:
        """获取同步 DB 管理器。required=False 时若不存在返回 None。"""
        with cls._lock:
            if db_name not in cls._bundles:
                if db_name == cls.__MAIN_DB_KEY and cls.__register_main_db_Listener:
                    cls.__register_main_db_Listener(db_name)  # 触发监听器注册，用户自行实现注册逻辑，最终会调用 register() 方法进行注册
                elif cls.__register_slave_DB_Listener:
                    cls.__register_slave_DB_Listener(db_name)

            bundle = cls._bundles.get(db_name)
            if not bundle or not bundle.sync:
                if required:
                    raise ValueError(cls._not_found_msg(db_name, want="sync"))
                return None
            return bundle.sync

    #  endregion

    #  region remark - 获取异步 DB 管理器
    @classmethod
    def get_async_db(cls, db_name: str = __MAIN_DB_KEY, *, required: bool = True) -> Optional[XAsyncDBManager]:
        """获取异步 DB 管理器（注意：这不是 async 函数）。"""
        with cls._lock:
            if db_name not in cls._bundles:
                if db_name == cls.__MAIN_DB_KEY and cls.__register_main_db_Listener:
                    cls.__register_main_db_Listener(db_name)  # 触发监听器注册，用户自行实现注册逻辑，最终会调用 register() 方法进行注册
                elif cls.__register_slave_DB_Listener:
                    cls.__register_slave_DB_Listener(db_name)

            bundle = cls._bundles.get(db_name)
            if not bundle or not bundle.async_:
                if required:
                    raise ValueError(cls._not_found_msg(db_name, want="async"))
                return None
            return bundle.async_

    # endregion

    # region remark - 维护/工具接口
    @classmethod
    def has_key(cls, key: str) -> bool:
        with cls._lock:
            return key in cls._bundles

    @classmethod
    def list_keys(cls) -> Iterable[str]:
        with cls._lock:
            return tuple(cls._bundles.keys())

    @classmethod
    def unregister(cls, key: str) -> None:
        with cls._lock:
            if key in cls._bundles:
                cls._bundles.pop(key, None)

    @classmethod
    def close_all(cls) -> None:
        """
        关闭所有连接（若管理器提供 close/cleanup 等接口，可以在此统一释放资源）。
        这里假设 XDBManager / XAsyncDBManager 暴露了 close()；若没有，可按你们类库实际情况修改。
        """
        with cls._lock:
            for b in cls._bundles.values():
                if getattr(b.sync, "close", None):
                    try:
                        b.sync.close()  # type: ignore[attr-defined]
                    except Exception:
                        pass
                if getattr(b.async_, "close", None):
                    try:
                        b.async_.close()  # type: ignore[attr-defined]
                    except Exception:
                        pass
            cls._bundles.clear()

    # —— 内部 —— #
    @classmethod
    def _not_found_msg(cls, key: str, want: str) -> str:
        keys = ", ".join(cls._bundles.keys()) or "<无>"
        return f"[XDBFactory] 未找到 {want} 数据库连接: '{key}'。可用 keys = {keys}"
    # endregion
