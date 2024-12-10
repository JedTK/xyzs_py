from sqlalchemy import Column, Integer, String

from xyzs_py.XBaseEntity import XBaseEntity, Base


class UserEntity(Base, XBaseEntity):
    __tablename__ = 'User'
    nickname = Column(String(64), nullable=False)

    def __repr__(self):
        return f"<User(id={self.id}, nickname={self.nickname})>"
