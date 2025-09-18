from xyzs_py.XLogs import XLogs
from xyzs_py.database.XDBConnect import XDBConnect

log = XLogs(__name__)


class XDBManager:
    """
    数据库管理器（读写分离封装）
    ========================

    设计目的：
    - 封装读库与写库的连接，避免业务层反复判断；
    - 提供统一入口获取 **ORM Session**（面向对象操作）和 **Core Connection**（原生 SQL 操作）；
    - 通过依赖注入，可灵活替换不同数据库配置（如主库/从库，MySQL/SQLite 等）。

    使用场景：
    --------
     # 初始化时分别传入写库与读库连接器
     write_db = XDBConnect("mysql+pymysql://u:p@master/db")
     read_db  = XDBConnect("mysql+pymysql://u:p@slave/db")
     dbm = XDBManager(write_connect=write_db, read_connect=read_db)

    【写操作（ORM 模式）】
     with dbm.get_write_session() as s:
         s.execute(text("INSERT INTO users(name) VALUES(:n)"), {"n": "Alice"})

    【读操作（ORM 模式）】
     with dbm.get_read_session() as s:
         rows = s.execute(text("SELECT * FROM users WHERE status=1")).mappings().all()
         for r in rows:
             print(r["id"], r["name"])

    【写操作（Core 模式）】
     with dbm.get_write_connect() as conn:
         with conn.begin():
             conn.execute(text("UPDATE users SET status=1 WHERE id=:id"), {"id": 100})

    【读操作（Core 模式）】
     with dbm.get_read_connect() as conn:
         rows = conn.execute(text("SELECT COUNT(*) AS c FROM users")).mappings().one()
         print("用户总数:", rows["c"])
    """

    def __init__(self, write_connect: XDBConnect = None, read_connect: XDBConnect = None):
        """
        :param write_connect: 写库连接包装（XDBConnect 实例，通常指主库）
        :param read_connect: 读库连接包装（XDBConnect 实例，通常指从库/只读库）
        """
        self.write_connect = write_connect
        self.read_connect = read_connect

    # ---------------------- ORM Session ----------------------

    def get_write_session(self):
        """获取写库 ORM 会话（带事务自动提交/回滚/关闭）"""
        if self.write_connect is None:
            log.error("写数据库连接未初始化")
            return None
        return self.write_connect.get_session()

    def get_read_session(self):
        """获取读库 ORM 会话（带事务自动提交/回滚/关闭）"""
        if self.read_connect is None:
            log.error("读数据库连接未初始化")
            return None
        return self.read_connect.get_session()

    # ---------------------- Core Connection ----------------------

    def get_write_connect(self):
        """获取写库 Core 连接（需显式控制事务，推荐 with conn.begin() 使用）"""
        if self.write_connect is None:
            log.error("写数据库连接未初始化")
            return None
        return self.write_connect.get_connect()

    def get_read_connect(self):
        """获取读库 Core 连接（需显式控制事务，推荐 with conn.begin() 使用）"""
        if self.read_connect is None:
            log.error("读数据库连接未初始化")
            return None
        return self.read_connect.get_connect()
