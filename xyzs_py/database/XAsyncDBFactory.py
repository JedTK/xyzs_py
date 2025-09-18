from __future__ import annotations

import inspect
from threading import RLock
from typing import Callable, Dict, Any

from xyzs_py.XLogs import XLogs
from xyzs_py.database import XAsyncDBConnect
from xyzs_py.database.XAsyncDBManager import XAsyncDBManager

log = XLogs(__name__)


class XAsyncDBFactory:
    """
    异步数据库工厂（只管理 XAsyncDBManager）
    - 以业务 key 存放异步 DB 管理器
    - 支持通过“监听器”在缺失时延迟注册（监听器可为同步或异步函数）
    - 线程安全；且不会在持锁时 await
    """

    _bundles: Dict[str, XAsyncDBManager] = {}
    _lock = RLock()

    __register_main_db_Listener: Callable[[str], Any] = None
    __register_slave_DB_Listener: Callable[[str], Any] = None

    __MAIN_DB_KEY = "main"

    # —— 监听器注入（同步方法即可；监听器本身可同步也可异步） —— #
    @classmethod
    def register_main_db(cls, register_main_db_Listener: Callable[[str], Any]):
        """注入主库注册监听器（监听器可为 sync 或 async 函数）"""
        log.info("注入主库注册监听器: %r", register_main_db_Listener)
        cls.__register_main_db_Listener = register_main_db_Listener

    @classmethod
    def register_slave_db(cls, register_slave_DB_Listener: Callable[[str], Any]):
        """注入从库注册监听器（监听器可为 sync 或 async 函数）"""
        log.info("注入从库注册监听器: %r", register_slave_DB_Listener)
        cls.__register_slave_DB_Listener = register_slave_DB_Listener

    @classmethod
    def register(cls,
                 db_name: str = __MAIN_DB_KEY,
                 write_connect: XAsyncDBConnect = None,
                 read_connect: XAsyncDBConnect = None) -> None:
        """
        注册异步数据库连接。
        overwrite=True：已存在则覆盖；False：已存在则直接返回不覆盖。
        """
        if write_connect is None or read_connect is None:
            raise ValueError("register 需要同时提供异步写/读数据库连接器。")

        log.info("注册异步数据库: %s", db_name)
        with cls._lock:
            db_manager = XAsyncDBManager(write_connect=write_connect, read_connect=read_connect)
            cls._bundles[db_name] = db_manager

    # 内部工具：在异步上下文里安全执行监听器（支持 sync/async）
    @staticmethod
    async def _invoke_listener_async(listener: Callable[[str], Any], db_name: str) -> None:
        ret = listener(db_name)
        if inspect.iscoroutine(ret):
            # 如果是异步协程，必须 await 或 asyncio.run(ret) 来执行
            await ret
        # 如果是普通函数，已经执行完成了，不用管

    @classmethod
    async def get_db(cls, db_name: str = __MAIN_DB_KEY, *, required: bool = True) -> XAsyncDBManager:
        """
        获取异步 DB 管理器（async）。
        不存在时：若配置了监听器，将在锁外触发监听器进行延迟注册（await 安全）。
        """
        # 第一次持锁：判断是否需要触发监听器，并取到监听器引用
        with cls._lock:
            need_register = db_name not in cls._bundles
            listener = None
            if need_register:
                if db_name == cls.__MAIN_DB_KEY and cls.__register_main_db_Listener:
                    listener = cls.__register_main_db_Listener
                elif cls.__register_slave_DB_Listener:
                    listener = cls.__register_slave_DB_Listener

        # 锁外：执行监听器（可能是 async），避免在持锁期间 await
        if listener is not None:
            await XAsyncDBFactory._invoke_listener_async(listener, db_name)

        # 第二次持锁：读取结果
        with cls._lock:
            bundle = cls._bundles.get(db_name)
            if not bundle and required:
                raise ValueError(f"[XAsyncDBFactory] 未找到 {db_name} 数据库连接")
            return bundle
