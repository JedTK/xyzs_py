from contextlib import asynccontextmanager
from typing import Optional, AsyncGenerator

from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncEngine,
    async_sessionmaker,
    AsyncSession,
    AsyncConnection,
)

from xyzs_py import XLogs

log = XLogs(__name__)


class XAsyncDBConnect:
    """
    异步数据库连接包装（AsyncIO 版本）
    =================================
    - 同步版 XDBConnect 的“异步等价物”，提供：
        1) ORM 会话（AsyncSession）→ 面向对象的业务读写，自动事务（成功提交/异常回滚）。
        2) Core 连接（AsyncConnection）→ 原生 SQL / 表达式，便于复杂报表、聚合与调优（推荐显式事务）。

    【什么时候用 ORM，什么时候用 Core？】
    - ORM：有实体关系、对象便利性（脏检查、级联）更重要的业务写入/查询。
    - Core：复杂 SQL/聚合/窗口函数/大报表/批处理/需要精准控制 SQL 与事务时更合适。

    【注意事项】
    - **不要混用** 同步与异步的 Engine/Session/Connection。
    - 每次请求/任务内按需创建会话或连接，`async with` 结束后自动释放；**不要跨协程长期持有**。
    - 连接池已启用 `pool_pre_ping=True`，减少“僵尸连接”问题（如 MySQL 空闲超时）。
    """

    def __init__(self,
                 host: str,
                 pool_size: int = 10,
                 max_overflow: int = 20,
                 pool_recycle: int = 1800,
                 echo_pool: bool | str = False,  # True/False 或 "debug"
                 echo: bool = False,
                 pool_timeout: int = 30,
                 expire_on_commit: bool = False):
        """
        :param host: 异步 DSN（非常重要：要用异步驱动）
                     MySQL  示例: "mysql+aiomysql://user:password@127.0.0.1:3306/db?charset=utf8mb4"
                     Postgres示例: "postgresql+asyncpg://user:password@127.0.0.1:5432/db"
        :param pool_size:     连接池常驻连接数
        :param max_overflow:  高峰期允许临时新增的连接数
        :param pool_recycle:  连接回收秒数（MySQL 常设 600~1800，配合 pre_ping 降低断链风险）
        :param echo_pool:     连接池日志（True/False 或 "debug"）
        :param echo:          SQL 执行日志（开发/排错可开 True）
        :param pool_timeout:  等待可用连接超时（秒）
        :param expire_on_commit: 提交后是否过期 ORM 对象缓存；默认 False 更友好
        """
        self.host = host
        self.pool_size = pool_size
        self.max_overflow = max_overflow
        self.pool_recycle = pool_recycle
        self.echo_pool = echo_pool
        self.echo = echo
        self.pool_timeout = pool_timeout
        self._expire_on_commit: bool = expire_on_commit

        self._engine: Optional[AsyncEngine] = None
        self._SessionFactory: Optional[async_sessionmaker[AsyncSession]] = None

    def __create_engine(self) -> AsyncEngine:
        """
        惰性创建或返回 AsyncEngine：
        - Engine 负责连接池与数据库方言管理；
        - `pool_pre_ping=True` 可在取用连接前探活，避免“服务器已断开”报错。
        """
        try:
            if self._engine is None:
                self._engine = create_async_engine(
                    self.host,
                    pool_size=self.pool_size,
                    max_overflow=self.max_overflow,
                    pool_recycle=self.pool_recycle,
                    pool_pre_ping=True,
                    pool_timeout=self.pool_timeout,
                    future=True,  # 2.0 风格
                    echo=self.echo,
                    echo_pool=self.echo_pool,
                )
            return self._engine
        except Exception as e:
            log.error(f"数据库连接失败: {e}")
            # 继续抛出，便于上层熔断/报警
            raise

    def __create_session(self) -> AsyncSession:
        """
        创建或返回一个 AsyncSession 实例（通过 async_sessionmaker 工厂创建）。
        - Session 是“工作单元（Unit of Work）”，承载 ORM 对象持久化与事务；
        - 不可跨协程复用；每次 `async with get_session()` 会新建一个新会话。
        """
        if self._SessionFactory is None:
            self._SessionFactory = async_sessionmaker(
                self.__create_engine(),
                expire_on_commit=self._expire_on_commit,
                future=True,
            )
        return self._SessionFactory()

    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """
        【ORM 会话上下文管理器】（推荐用于面向对象的业务读写）

        使用示例（ORM）：
        ----------------
         db = XAsyncDBConnect("mysql+aiomysql://u:p@127.0.0.1:3306/app?charset=utf8mb4")
         async with db.get_session() as s:
             # 2.0 风格执行 SQL（推荐）
             rows = (await s.execute(text("SELECT id, name FROM users WHERE status=:st"), {"st": 1})) \
                    .mappings().all()
             for r in rows:
                 print(r["id"], r["name"])

             # 写操作示例：
             # await s.execute(text("INSERT INTO users(name) VALUES (:n)"), {"n": "Alice"})
             # 离开 async with：正常→自动 commit；异常→自动 rollback

        事务语义：
        - 正常退出 → 自动 `commit()`
        - 发生异常 → 自动 `rollback()` 并向上抛出
        - 结束后自动 `close()`，无需手动管理资源
        """
        session = self.__create_session()
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            raise e
        finally:
            await session.close()

    @asynccontextmanager
    async def get_connect(self) -> AsyncGenerator[AsyncConnection, None]:
        """
        【Core 连接上下文管理器】（适合原生 SQL / 表达式、报表/聚合/批处理）

        使用示例 A：显式事务（强烈推荐）
        --------------------------------
         async with db.get_connect() as conn:
             async with conn.begin():  # 成功自动 commit，异常自动 rollback
                 await conn.execute(text("UPDATE users SET status=1 WHERE id=:id"), {"id": 100})

        使用示例 B：只读查询（无需事务也可，但建议统一风格）
        ----------------------------------------------
         async with db.get_connect() as conn:
             rows = (await conn.execute(text("SELECT COUNT(*) AS c FROM users"))).mappings().one()
             print("用户总数:", rows["c"])

        说明：
        - Core 的事务需要**显式控制**（`async with conn.begin():`），原子性可控、行为更一致；
        - 不包事务时，部分方言有自动提交/开启策略，但不利于一致性与调试，建议统一显式事务。
        """
        engine = self.__create_engine()
        conn: AsyncConnection = await engine.connect()  # 异步连接：必须 await
        try:
            yield conn
        finally:
            await conn.close()  # 归还连接到连接池

    async def dispose(self) -> None:
        """
        关闭连接池（优雅下线）。
        在 FastAPI/服务退出时调用：await db.dispose()
        """
        if self._engine is not None:
            await self._engine.dispose()
