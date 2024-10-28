import asyncio
import os
import sys

from xyzs_py.XLogs import XLogs
from xyzs_py.XConfig import XConfig
from xyzs_py.XCache import XCache

log = XLogs('FFmpeg')

async def main():
    # 载入配置文件
    XConfig.init("./config", os.getenv("ENV", "config"))
    # 初始化Redis连接，确保全局唯一实例
    XCache.initialize(host=XConfig.get("redis.host"),
                      port=XConfig.get("redis.port"),
                      password=XConfig.get("redis.password"),
                      db=XConfig.get("redis.db"),
                      expire=XConfig.get("redis.expire"),
                      prefix=XConfig.get("redis.prefix"))



    try:
        while True:
            await asyncio.sleep(3600)
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    print(f" <<<<< {__name__} 启动 -- Python:{sys.version} ENV:{os.getenv('ENV')} >>>>>")
    log.info(f" <<<<< {__name__} 启动 -- Python:{sys.version} ENV:{os.getenv('ENV')} >>>>>")
    asyncio.run(main())