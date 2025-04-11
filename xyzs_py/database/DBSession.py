import contextlib
import os
from contextlib import AbstractContextManager
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

# 全局变量，用于存储写库和读库的会话工厂
_lazy_write_session = None  # 延迟初始化的写库会话工厂
_lazy_read_session = None  # 延迟初始化的读库会话工厂


def __create_session(engine_url: str
                   , pool_size: int
                   , max_overflow: int
                   , pool_recycle: int
                   , echo: False,
                   echo_pool: False) -> sessionmaker:
    """
    创建SQLAlchemy会话工厂。


    :param engine_url: 数据库连接字符串，例如"mysql+pymysql://user:password@localhost/dbname"。
    :param pool_size: 数据库连接池大小。
    :param max_overflow: 连接池最大溢出连接数。
    :param pool_recycle: 连接回收时间，单位秒。
    :param echo: 是否输出日志
    :param echo_pool: 是否输出日志
    :return: 用于创建会话的sessionmaker实例。
    """
    engine = create_engine(
        engine_url,
        pool_size=pool_size,
        max_overflow=max_overflow,
        pool_recycle=pool_recycle,
        pool_pre_ping=True,  # 在连接之前检测其是否可用
        future=True,  # 使用SQLAlchemy 2.0风格
        echo=echo,
        echo_pool=echo_pool,
    )
    return sessionmaker(bind=engine)


def get_write_session_factory() -> sessionmaker:
    """
    获取写库的会话工厂，支持延迟初始化。

    :return: 写库的sessionmaker实例。
    """
    global _lazy_write_session
    if _lazy_write_session is None:
        # 从配置文件中获取写库连接参数
        host = os.getenv("SQLALCHEMY.DATABASE.WRITE.HOST")
        pool_size = int(os.getenv("SQLALCHEMY.WRITE.POOL.SIZE", default=5))
        max_size = int(os.getenv("SQLALCHEMY.WRITE.POOL.MAX_SIZE", default=10))
        recycle = int(os.getenv("SQLALCHEMY.WRITE.POOL.RECYCLE", default=1800))
        echo_pool = bool(int(os.getenv("SQLALCHEMY.WRITE.POOL.ECHO", default=0)))
        echo = bool(int(os.getenv("SQLALCHEMY.DATABASE.ECHO", default=0)))
        _lazy_write_session = __create_session(host, pool_size, max_size, recycle, echo, echo_pool)
    return _lazy_write_session


def get_read_session_factory() -> sessionmaker:
    """
    获取读库的会话工厂，支持延迟初始化。

    :return: 读库的sessionmaker实例。
    """
    global _lazy_read_session
    if _lazy_read_session is None:
        # 从配置文件中获取读库连接参数
        host = os.getenv("SQLALCHEMY.DATABASE.READ.HOST")
        pool_size = int(os.getenv("SQLALCHEMY.READ.POOL.size", default=5))
        max_size = int(os.getenv("SQLALCHEMY.READ.POOL.max_size", default=10))
        recycle = int(os.getenv("SQLALCHEMY.READ.POOL.recycle", default=1800))
        echo = bool(os.getenv("SQLALCHEMY.DATABASE.ECHO", default=0))
        echo_pool = bool(os.getenv("SQLALCHEMY.READ.POOL.echo", default=0))
        _lazy_read_session = __create_session(host, pool_size, max_size, recycle, echo, echo_pool)
    return _lazy_read_session


@contextlib.contextmanager
def get_session(session_maker: sessionmaker) -> Generator[Session, None, None]:
    """
    通用的SQLAlchemy会话上下文管理器，用于管理数据库会话的创建和释放。

    :param session_maker: sessionmaker实例，用于创建会话。
    :yield: 数据库会话实例。
    """
    session = session_maker()  # 创建会话
    try:
        yield session  # 提供会话给调用者使用
        session.commit()  # 提交事务
    except Exception as e:
        session.rollback()  # 回滚事务，防止数据不一致
        raise e  # 将异常继续抛出
    finally:
        session.close()  # 关闭会话，释放资源


def get_write_session() -> AbstractContextManager[Session]:
    """
    获取写库的会话上下文管理器，用于处理写操作。

    :return: 写库会话的上下文管理器。
    """
    return get_session(get_write_session_factory())


def get_read_session() -> AbstractContextManager[Session]:
    """
    获取读库的会话上下文管理器，用于处理读操作。

    :return: 读库会话的上下文管理器。
    """
    return get_session(get_read_session_factory())
