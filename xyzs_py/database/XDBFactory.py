from __future__ import annotations

import asyncio
import inspect
from threading import RLock
from typing import Callable, Dict, Optional

from xyzs_py.XLogs import XLogs
from xyzs_py.database import XDBConnect
from xyzs_py.database.XDBManager import XDBManager

log = XLogs(__name__)


class XDBFactory:
    """
    同步数据库工厂（只管理 XDBManager）
    - 以业务 key 存放同步 DB 管理器
    - 支持通过“监听器”在缺失时延迟注册（监听器可为同步或异步函数）
    - 避免在持锁期间 await；如监听器为异步函数，将在无事件循环时用 asyncio.run() 执行
    """

    _bundles: Dict[str, XDBManager] = {}
    _lock = RLock()

    __register_main_db_Listener: Optional[Callable[[str], object]] = None
    __register_slave_DB_Listener: Optional[Callable[[str], object]] = None

    __MAIN_DB_KEY = "main"

    @classmethod
    def register_main_db(cls, register_main_db_Listener: Callable[[str], object]):
        log.info("注入主库注册监听器: %r", register_main_db_Listener)
        cls.__register_main_db_Listener = register_main_db_Listener

    @classmethod
    def register_slave_db(cls, register_slave_DB_Listener: Callable[[str], object]):
        log.info("注入从库注册监听器: %r", register_slave_DB_Listener)
        cls.__register_slave_DB_Listener = register_slave_DB_Listener

    @classmethod
    def register(cls,
                 db_name: str = __MAIN_DB_KEY,
                 write_connect: Optional[XDBConnect] = None,
                 read_connect: Optional[XDBConnect] = None) -> None:
        """
        注册同步数据库连接。
        overwrite=True：已存在则覆盖；False：已存在则直接返回不覆盖。
        """
        if write_connect is None or read_connect is None:
            raise ValueError("register 需要同时提供同步写/读数据库连接器。")

        log.info("注册同步数据库: %s", db_name)
        with cls._lock:
            db_manager = XDBManager(write_connect=write_connect, read_connect=read_connect)
            cls._bundles[db_name] = db_manager

    # 内部工具：在“同步上下文”中执行监听器（支持 sync/async）
    @staticmethod
    def _invoke_listener_sync(listener: Callable[[str], object], db_name: str) -> None:
        ret = listener(db_name)
        if inspect.iscoroutine(ret):
            # 同步上下文中执行异步监听器：仅在没有事件循环时允许
            try:
                loop = asyncio.get_running_loop()
                if loop.is_running():
                    raise RuntimeError(
                        "检测到正在运行的事件循环：请在异步上下文中使用异步 API 获取，或改为异步监听器由调用方 await。")
            except RuntimeError:
                # 没有运行中的事件循环 -> 安全执行
                asyncio.run(ret)

    @classmethod
    def get_db(cls, db_name: str = __MAIN_DB_KEY, *, required: bool = True) -> XDBManager:
        """
        获取同步 DB 管理器（sync）。
        不存在时：若配置了监听器，将在锁外触发监听器进行延迟注册。
        若监听器为 async 且检测到当前线程已有事件循环在跑，会明确抛错引导使用异步获取方式。
        """
        with cls._lock:
            need_register = db_name not in cls._bundles
            listener = None
            if need_register:
                if db_name == cls.__MAIN_DB_KEY and cls.__register_main_db_Listener:
                    listener = cls.__register_main_db_Listener
                elif cls.__register_slave_DB_Listener:
                    listener = cls.__register_slave_DB_Listener

        if listener is not None:
            cls._invoke_listener_sync(listener, db_name)

        with cls._lock:
            bundle = cls._bundles.get(db_name)
            if not bundle and required:
                raise ValueError(f"[XDBFactory] 未找到 {db_name} 数据库连接")
            return bundle
