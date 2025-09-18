from contextlib import contextmanager
from typing import Optional, Generator

from sqlalchemy import create_engine, Engine, Connection
from sqlalchemy.orm import sessionmaker, Session

from xyzs_py.XLogs import XLogs

log = XLogs(__name__)


class XDBConnect:
    """
    数据库连接包装（同步版）
    ========================

    该类同时提供：
    1) **ORM 会话（Session）**：用于面向对象的增删改查，自动管理事务边界（with 代码块成功→commit，异常→rollback）。
    2) **Core 连接（Connection）**：用于编写原生 SQL 或 SQL 表达式（`text()`、`select()` 等），更贴近数据库语义，便于做复杂报表/聚合/调优。

    【ORM vs Core 选型建议】
    - **ORM**：适合有实体/关系的业务写入与查询；需要脏检查、级联、对象映射等便利性时用。
    - **Core**：适合复杂 SQL、聚合/窗口函数、报表统计、高性能批量写入/只读查询；SQL 可控、可复用数据库特性。

    【线程与生命周期】
    - `Engine` 是**线程安全**的、全局复用；`sessionmaker` 也是线程安全的**工厂**；
    - **不要跨线程复用同一个 Session/Connection**；每个线程/请求都应新建并在 with 结束后释放。

    【连接池参数说明（MySQL 方向）】
    - `pool_size`：连接池常驻连接数（Web 服务常见 5~20）。
    - `max_overflow`：超过池上限时可临时再创建的连接数（峰值过后会回收）。
    - `pool_recycle`：连接存活秒数；MySQL 常设置 600~1800，避免“服务器关闭闲置连接”导致的失效。
    - `pool_pre_ping=True`：借助心跳检查避免“僵尸连接”。
    - `pool_timeout`：池中无可用连接时等待的秒数（超时抛异常，避免无限阻塞）。
    - `echo`/`echo_pool`：调试日志；`echo_pool` 可为 `"debug"` 以输出更详细的池事件。

    用法速览
    --------
    【ORM 场景】（自动事务）
    db = XDBConnect("mysql+pymysql://user:pwd@host:3306/db?charset=utf8mb4")
    with db.get_session() as s:
         # 1) 对象化操作（举例）
         # s.add(User(name="Alice"))
         # 2) 2.0 风格查询/执行
         rows = s.execute(text("SELECT id, name FROM users WHERE status=:st"), {"st": 1}).mappings().all()
         for r in rows:
             print(r["id"], r["name"])
    # 正常结束会自动 commit；异常会 rollback

    【Core 场景】（推荐显式事务）
    with db.get_connect() as conn:
        # 读-only（不包事务也行，但推荐显式事务，尤其涉及写入时）
        with conn.begin():  # 打开一个事务；离开 with 自动 commit（异常则自动 rollback）
            rows = conn.execute(text("SELECT COUNT(*) AS c FROM users WHERE status=:st"), {"st": 1}).mappings().one()
            print("count=", rows["c"])
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
        :param host: 数据库连接字符串（DSN），例如：
                     "mysql+pymysql://user:password@127.0.0.1:3306/dbname?charset=utf8mb4"
        :param pool_size: 连接池大小（常驻连接数）
        :param max_overflow: 连接池最大溢出连接数（高峰期临时创建）
        :param pool_recycle: 连接回收时间（秒），超过后下次使用前先回收重建，避免 MySQL 空闲超时
        :param echo_pool: 连接池日志（True/False 或 "debug"）
        :param echo: SQL 执行日志（开发/排错时可设 True）
        :param pool_timeout: 等待可用连接的超时（秒）
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

        self._engine: Optional[Engine] = None
        self._SessionFactory: Optional[sessionmaker] = None

    def __create_engine(self) -> Engine:
        """
        创建或返回全局 Engine（惰性初始化）
        - Engine 负责连接池与数据库方言管理；
        - 这里开启了 pool_pre_ping，以减少“连接已断开”的报错。
        """
        try:
            if self._engine is None:
                self._engine = create_engine(
                    self.host,
                    pool_size=self.pool_size,
                    max_overflow=self.max_overflow,
                    pool_recycle=self.pool_recycle,
                    pool_pre_ping=True,
                    pool_timeout=self.pool_timeout,
                    future=True,  # 使用 SQLAlchemy 2.0 风格 API
                    echo=self.echo,
                    echo_pool=self.echo_pool,
                )
            return self._engine
        except Exception as e:
            # 这里捕获创建引擎异常（如 DSN 错误、驱动缺失等）
            log.error(f"数据库连接失败: {e}")
            # 继续抛出更利于上层熔断/报警；也可以选择返回 None 自行判空
            raise

    def __create_session(self) -> Session | None:
        """
        创建或返回一个 ORM Session 实例（通过 sessionmaker 工厂创建）。
        说明：
        - Session 是“工作单元（Unit of Work）”，承载 ORM 对象的持久化状态与事务；
        - 不可跨线程复用；每次 `with get_session()` 都会新建一个全新的 Session。
        """
        try:
            if self._SessionFactory is None:
                self._SessionFactory = sessionmaker(bind=self.__create_engine(),
                                                    expire_on_commit=self._expire_on_commit,
                                                    future=True)
            return self._SessionFactory()
        except  Exception as e:
            log.error(f"数据库会话工厂创建失败: {e}")
            raise

    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """
        【ORM 会话上下文管理器】（推荐用于面向对象的业务读写）
        使用模式：
        with db.get_session() as s:
            # 写操作：s.add()/s.delete()/s.execute(INSERT ...)，离开 with 自动提交
            # 读操作：s.execute(select(...)) / s.get(User, 1) / s.query(...)（2.0 建议用 select/execute）
            pass

        事务语义：
        - 正常退出 with → 自动 `commit()`
        - 发生异常 → 自动 `rollback()`，异常继续向上抛出
        - 无需手动 close，with 结束自动 `close()`

        小贴士：
        - **只读查询**：即使没有写入，默认也会在退出时 commit 一下（2.0 的事务自动开始机制），这是安全的；
        - 若确有“超大只读报表”且需要更细的控制，可考虑换用 Core 连接（`get_connect()`）。
        """
        session = self.__create_session()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    @contextmanager
    def get_connect(self) -> Generator[Connection, None, None]:
        """
        【Core 连接上下文管理器】（推荐用于原生 SQL / 表达式、报表与复杂聚合）
        使用模式 A：显式事务（推荐）
        with db.get_connect() as conn:
            with conn.begin():  # 开启显式事务块
                conn.execute(text("UPDATE users SET status=1 WHERE id=:id"), {"id": 100})

        使用模式 B：只读/临时查询
        with db.get_connect() as conn:
            rows = conn.execute(text("SELECT id,name FROM users WHERE status=:s"), {"s": 1}).mappings().all()
             for r in rows:
                print(r["id"], r["name"])

        说明：
        - Core 的事务需要你**自行控制**。建议一律 `with conn.begin()` 包住需要原子性的一组语句；
        - `with conn.begin()` 正常结束会自动 commit，异常会自动 rollback；
        - 不包事务时，部分方言下会采用自动提交/自动开启策略，但**不利于可控性与一致性**，因此推荐显式事务。
        """
        engine = self.__create_engine()  # 确保惰性初始化已发生（修复 _engine 可能为 None 的情况）
        conn: Connection = engine.connect()  # 取一个连接（来自连接池）
        try:
            yield conn
        finally:
            conn.close()  # 归还给连接池（不是物理关闭）

    def dispose(self) -> None:
        """
        关闭连接池（优雅下线用）。
        FastAPI/服务退出时可调用：await adb.dispose()
        """
        if self._engine is not None:
            self._engine.dispose()
