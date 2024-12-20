import asyncio
import os
import sys

from sqlalchemy.exc import SQLAlchemyError

from tests.service.TestService import TestService
from xyzs_py.XLogs import XLogs
from xyzs_py.XConfig import XConfig
from xyzs_py.XCache import XCache

log = XLogs('tests')


async def main():
    # 载入配置文件
    XConfig.init("./tests/config", os.getenv("ENV", "config"))
    # 初始化Redis连接，确保全局唯一实例
    XCache.initialize(host=XConfig.getStr("redis.host", "127.0.0.1"),
                      port=XConfig.getInt("redis.port", 6379),
                      password=XConfig.getStr("redis.password", ''),
                      db=XConfig.getInt("redis.db", 0),
                      expire=XConfig.getInt("redis.expire", 3600000),
                      prefix=XConfig.getStr("redis.prefix", ''))
    try:
        # user = UserEntity()
        # user.nickname = "kitty"
        # with get_write_session() as session:
        #     session.add(user)  # 提交事务在上下文管理器中自动完成
        # print("用户插入成功")

        XCache.set("test", 1)
        v = XCache.get("test")
        print(v)

        await TestService().test()

    except SQLAlchemyError as e:
        print(f"数据库操作失败: {e}")


# try:
#     while True:
#         await asyncio.sleep(3600)
# except KeyboardInterrupt:
#     pass

if __name__ == '__main__':
    print(f" <<<<< {__name__} 启动 -- Python:{sys.version} "
          # f"Path:{sys.path} "
          f"ENV:{os.getenv('ENV', 'config')} >>>>>")
    asyncio.run(main())
