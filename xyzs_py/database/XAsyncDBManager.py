from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional, Any

from sqlalchemy.ext.asyncio import AsyncSession, AsyncConnection
from xyzs_py import XLogs
from xyzs_py.database.XAsyncDBConnect import XAsyncDBConnect

log = XLogs(__name__)


class XAsyncDBManager:
    """
    异步数据库管理器（读写分离封装）
    ==============================

    设计目的：
    - 封装读库与写库的连接，避免业务层反复判断；
    - 提供统一入口获取 **ORM AsyncSession** 和 **AsyncConnection**；
    - 通过依赖注入，可灵活替换不同数据库配置（主库/从库，MySQL/Postgres 等）。

    使用场景：
    --------
     write_db = XAsyncDBConnect("mysql+aiomysql://u:p@master/db")
     read_db  = XAsyncDBConnect("mysql+aiomysql://u:p@slave/db")
     adb = XAsyncDBManager(write_connect=write_db, read_connect=read_db)

    【写操作（ORM 模式）】
     async with adb.get_write_session() as s:
         await s.execute(text("INSERT INTO users(name) VALUES(:n)"), {"n": "Alice"})

    【读操作（ORM 模式）】
     async with adb.get_read_session() as s:
         rows = (await s.execute(text("SELECT * FROM users WHERE status=1"))).mappings().all()
         for r in rows:
             print(r["id"], r["name"])

    【写操作（Core 模式）】
     async with adb.get_write_connect() as conn:
         async with conn.begin():
             await conn.execute(text("UPDATE users SET status=1 WHERE id=:id"), {"id": 100})

    【读操作（Core 模式）】
     async with adb.get_read_connect() as conn:
         row = (await conn.execute(text("SELECT COUNT(*) AS c FROM users"))).mappings().one()
         print("用户总数:", row["c"])
    """

    def __init__(self, write_connect: Optional[XAsyncDBConnect] = None,
                 read_connect: Optional[XAsyncDBConnect] = None):
        self.write_connect = write_connect
        self.read_connect = read_connect

    # ---------------------- ORM Session ----------------------

    @asynccontextmanager
    async def get_write_session(self):
        """获取写库 AsyncSession（自动提交/回滚/关闭）"""
        if self.write_connect is None:
            log.error("写数据库连接未初始化")
            yield None
            return
        async with self.write_connect.get_session() as s:
            yield s

    @asynccontextmanager
    async def get_read_session(self):
        """获取读库 AsyncSession（自动提交/回滚/关闭）"""
        if self.read_connect is None:
            log.error("读数据库连接未初始化")
            yield None
            return
        async with self.read_connect.get_session() as s:
            yield s

    # ---------------------- Core Connection ----------------------

    @asynccontextmanager
    async def get_write_connect(self):
        """获取写库 AsyncConnection（推荐 async with conn.begin() 包事务）"""
        if self.write_connect is None:
            log.error("写数据库连接未初始化")
            yield None
            return
        async with self.write_connect.get_connect() as c:
            yield c

    @asynccontextmanager
    async def get_read_connect(self):
        """获取读库 AsyncConnection（推荐 async with conn.begin() 包事务）"""
        if self.read_connect is None:
            log.error("读数据库连接未初始化")
            yield None
            return
        async with self.read_connect.get_connect() as c:
            yield c
