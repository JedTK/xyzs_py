import json
from sqlalchemy import Column, Integer
from sqlalchemy.ext.declarative import declarative_base, declared_attr
from sqlalchemy.inspection import inspect


def target_db(db_name: str):
    """类装饰器：给实体类绑定数据库 key"""

    def decorator(cls):
        cls.__bind_key__ = db_name
        return cls

    return decorator


class XBaseEntity:
    """所有实体类的基础功能"""
    id = Column(Integer, primary_key=True)

    @classmethod
    def get_db_name(cls) -> str:
        """获取类绑定的数据库名，默认为 main"""
        return getattr(cls, "__bind_key__", "main")

    def to_dict(self) -> dict:
        """转为字典"""
        return {c.key: getattr(self, c.key) for c in inspect(self).mapper.column_attrs}

    def to_json(self) -> str:
        """转为 JSON 字符串"""
        return json.dumps(self.to_dict(), ensure_ascii=False)

    def __repr__(self):
        cls_name = self.__class__.__name__
        return f"<{cls_name} id={self.id}>"


class BaseWithAutoTableName:
    """自动生成表名的基类，不做大小写/下划线转换"""

    @declared_attr
    def __tablename__(cls):
        if cls.__name__.endswith("Entity"):
            return cls.__name__[:-6]  # 去掉 Entity 后缀
        return cls.__name__


# 组合成全局 Base
Base = declarative_base(cls=type("BaseModel", (BaseWithAutoTableName, XBaseEntity), {}))
