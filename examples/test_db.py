from xyzs_py.database import XDBConnect
from xyzs_py.database.XDBManager import XDBManager

write_connect = XDBConnect(host="", pool_size=5, max_size=10, recycle=3600, echo_pool=False, echo=False)
read_connect = XDBConnect(host="", pool_size=5, max_size=10, recycle=3600, echo_pool=False, echo=False)
db = XDBManager(write_connect=write_connect, read_connect=read_connect)
with db.get_read_session() as session:
    session.query("").all()
    pass
