from __future__ import annotations

from dataclasses import dataclass
from threading import RLock
from typing import Dict, Optional, Iterable

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

    def __init__(self) -> None:
        self._bundles: Dict[str, DBBundle] = {}
        self._lock = RLock()

    def register(self,
                 key: str = "default",
                 write_connect: Optional[XDBConnect] = None,
                 read_connect: Optional[XDBConnect] = None,
                 write_async_connect: Optional[XAsyncDBConnect] = None,
                 read_async_connect: Optional[XAsyncDBConnect] = None,
                 overwrite: bool = True) -> None:
        """
        注册数据库连接：
        - 可只传同步（write_connect+read_connect）
        - 可只传异步（write_async_connect+read_async_connect）
        - 也可两者都传
        overwrite=True：重复注册会覆盖对应部分；False：若已存在则抛异常
        """
        if not any([write_connect and read_connect, write_async_connect and read_async_connect]):
            raise ValueError("register 需要同时提供同步写/读 或 异步写/读 中的至少一组。")

        with self._lock:
            bundle = self._bundles.get(key, DBBundle())

            # 同步
            if write_connect is not None or read_connect is not None:
                if not (write_connect and read_connect):
                    raise ValueError("同步注册需要同时提供 write_connect 和 read_connect。")
                if bundle.sync is not None and not overwrite:
                    raise ValueError(f"Key='{key}' 已存在同步管理器，且 overwrite=False。")
                bundle.sync = XDBManager(write_connect=write_connect, read_connect=read_connect)

            # 异步
            if write_async_connect is not None or read_async_connect is not None:
                if not (write_async_connect and read_async_connect):
                    raise ValueError("异步注册需要同时提供 write_async_connect 和 read_async_connect。")
                if bundle.async_ is not None and not overwrite:
                    raise ValueError(f"Key='{key}' 已存在异步管理器，且 overwrite=False。")
                bundle.async_ = XAsyncDBManager(write_connect=write_async_connect,
                                                read_connect=read_async_connect)

            self._bundles[key] = bundle.ensure_any()

    # —— 获取接口 —— #
    def get_sync_db(self, key: str = "default", *, required: bool = True) -> Optional[XDBManager]:
        """获取同步 DB 管理器。required=False 时若不存在返回 None。"""
        with self._lock:
            bundle = self._bundles.get(key)
            if not bundle or not bundle.sync:
                if required:
                    raise ValueError(self._not_found_msg(key, want="sync"))
                return None
            return bundle.sync

    def get_async_db(self, key: str = "default", *, required: bool = True) -> Optional[XAsyncDBManager]:
        """获取异步 DB 管理器（注意：这不是 async 函数）。"""
        with self._lock:
            bundle = self._bundles.get(key)
            if not bundle or not bundle.async_:
                if required:
                    raise ValueError(self._not_found_msg(key, want="async"))
                return None
            return bundle.async_

    # —— 维护/工具接口 —— #
    def has_key(self, key: str) -> bool:
        with self._lock:
            return key in self._bundles

    def list_keys(self) -> Iterable[str]:
        with self._lock:
            return tuple(self._bundles.keys())

    def unregister(self, key: str) -> None:
        with self._lock:
            if key in self._bundles:
                self._bundles.pop(key, None)

    def close_all(self) -> None:
        """
        关闭所有连接（若管理器提供 close/cleanup 等接口，可以在此统一释放资源）。
        这里假设 XDBManager / XAsyncDBManager 暴露了 close()；若没有，可按你们类库实际情况修改。
        """
        with self._lock:
            for b in self._bundles.values():
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
            self._bundles.clear()

    # —— 内部 —— #
    def _not_found_msg(self, key: str, want: str) -> str:
        keys = ", ".join(self._bundles.keys()) or "<无>"
        return f"[XDBFactory] 未找到 {want} 数据库连接: '{key}'。可用 keys = {keys}"
