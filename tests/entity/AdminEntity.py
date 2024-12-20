from sqlalchemy import Column, BigInteger, String, Integer
from xyzs_py.XBaseEntity import XBaseEntity, Base


class AdminEntity(Base, XBaseEntity):
    """
    管理员基础表实体类，用于存储管理员的基础信息。
    """

    # 管理员姓名
    name = Column(String(64), nullable=False, default="", comment="管理员姓名")

    # 手机号码，注册必填
    phone = Column(String(20), nullable=False, default="", comment="手机号码，注册必填")

    # email
    email = Column(String(64), nullable=False, default="", comment="email")

    # 状态
    status = Column(Integer, nullable=False, default=0, comment="状态")

    # 创建IP
    create_ip = Column(String(20), nullable=False, default="", comment="创建IP")

    # 创建时间
    create_time = Column(BigInteger, nullable=False, default=0, comment="创建时间")

    # 更新时间
    update_time = Column(BigInteger, nullable=False, default=0, comment="更新时间")

    def __repr__(self):
        """
        定义对象的字符串表示形式，方便调试和日志记录。

        :return: 包含管理员ID、姓名和手机号的字符串。
        """
        return f"<AdminEntity id={self.id}, name={self.name}, phone={self.phone}>"
