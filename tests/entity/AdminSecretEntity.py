from sqlalchemy import Column, BigInteger, String
from xyzs_py.XBaseEntity import XBaseEntity, Base


class AdminSecretEntity(Base, XBaseEntity):
    """
    管理员密钥表实体类，用于存储管理员的密码和加密秘钥。
    """

    # 管理员ID
    admin_id = Column(BigInteger, nullable=False, default=0, comment="管理员ID")

    # 密码
    password = Column(String(32), nullable=False, comment="密码")

    # 秘钥
    password_secret = Column(String(32), nullable=False, comment="秘钥")

    def __repr__(self):
        """
        定义对象的字符串表示形式，方便调试和日志记录。

        :return: 包含密钥记录ID和管理员ID的字符串。
        """
        return f"<AdminSecretEntity id={self.id}, admin_id={self.admin_id}>"