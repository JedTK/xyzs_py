from xyzs_py.XCache import XCache


class TestService:
    @staticmethod
    async def test():
        XCache.set("test1", 2)
        v = XCache.get("test1")
        print(v)
