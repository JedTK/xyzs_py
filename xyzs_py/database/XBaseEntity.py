from sqlalchemy import Column, Integer
from sqlalchemy.ext.declarative import declarative_base, declared_attr
from sqlalchemy.inspection import inspect


class XBaseEntity:
    """
    Entity的基类，所有Entity都必须继承。
    提供了通用的id字段和实体转字典的方法。
    """
    id = Column(Integer, primary_key=True)  # 主键字段

    def to_dict(self):
        """
        将实体对象转换为字典。

        :return: 包含实体所有属性及其值的字典。
        """
        return {c.key: getattr(self, c.key) for c in inspect(self).mapper.column_attrs}


class BaseWithAutoTableName:
    """
    自动生成表名的基类。
    如果类名以"Entity"结尾，将类名前缀的小写部分作为表名。
    """

    @declared_attr
    def __tablename__(self):
        if self.__name__.endswith("Entity"):
            return self.__name__[:-6]  # 移除"Entity"后缀并转为小写
        return self.__name__


# 使用 declarative_base 创建一个新的基础类
Base = declarative_base(cls=BaseWithAutoTableName)
