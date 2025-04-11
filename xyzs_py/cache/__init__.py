from .XCacheFactory import XCacheFactory

# 对外暴露 XCache 实例获取接口
get_cache = XCacheFactory.get_default
create_cache = XCacheFactory.create
delete_cache = XCacheFactory.delete

__all__ = [
    "get_cache",
    "create_cache",
    "delete_cache"
]
