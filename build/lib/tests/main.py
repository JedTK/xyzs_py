import asyncio
import os
import sys

from sqlalchemy.exc import SQLAlchemyError

from tests.entity.UserEntity import UserEntity
from xyzs_py.XBaseEntity import get_write_session
from xyzs_py.XLogs import XLogs
from xyzs_py.XConfig import XConfig
from xyzs_py.XCache import XCache

log = XLogs('tests')


async def main():
    # 载入配置文件
    XConfig.init("./tests/config", os.getenv("ENV", "config"))
    # 初始化Redis连接，确保全局唯一实例
    XCache.initialize(host=XConfig.get("redis.host"),
                      port=XConfig.get("redis.port"),
                      password=XConfig.get("redis.password"),
                      db=XConfig.get("redis.db"),
                      expire=XConfig.get("redis.expire"),
                      prefix=XConfig.get("redis.prefix"))
    try:
        user = UserEntity()
        user.nickname = "kitty"
        with get_write_session() as session:
            session.add(user)  # 提交事务在上下文管理器中自动完成
        print("用户插入成功")
    except SQLAlchemyError as e:
        print(f"数据库操作失败: {e}")

    try:
        while True:
            await asyncio.sleep(3600)
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    print(f" <<<<< {__name__} 启动 -- Python:{sys.version} "
          # f"Path:{sys.path} "
          f"ENV:{os.getenv('ENV', 'config')} >>>>>")
    asyncio.run(main())
