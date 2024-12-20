from sqlalchemy import Column, BigInteger, String, Text, Integer
from xyzs_py.XBaseEntity import XBaseEntity, Base


class DeviceEntity(Base, XBaseEntity):
    """
    设备实体类，表示设备相关的数据。
    """

    # 设备序列号
    serial_number = Column(BigInteger, nullable=False, default=0, comment="设备序列号")

    # SPU编码
    spu_code = Column(String, nullable=False, default="", comment="SPU编码")

    # 品牌编码
    brand_code = Column(String, nullable=False, default="", comment="品牌编码")

    # 类型编码
    type_code = Column(String, nullable=False, default="", comment="类型编码")

    # 在线状态：0-离线，1-在线
    online_status = Column(Integer, nullable=False, default=0, comment="在线状态:0-离线，1-在线")

    # 状态
    status = Column(Integer, nullable=False, default=0, comment="状态")

    # 描述
    description = Column(String(900), nullable=False, comment="描述")

    # 管理员ID
    admin_id = Column(BigInteger, nullable=False, default=0, comment="管理员ID")

    # 规格，JSON结构
    spec = Column(Text, nullable=False, comment="规格，JSON结构")

    # 动态信息，JSON结构
    dynamic_data = Column(Text, nullable=False, comment="动态信息，JSON结构")

    # 配置，JSON结构
    config = Column(Text, nullable=False, comment="配置，JSON结构")

    # 创建时间
    create_time = Column(BigInteger, nullable=False, default=0, comment="创建时间")

    # 更新时间
    update_time = Column(BigInteger, nullable=False, default=0, comment="更新时间")

    def __repr__(self):
        """
        定义对象的字符串表示形式，方便调试和日志记录。

        :return: 包含设备ID和序列号的字符串。
        """
        return f"<id={self.id}, serial_number={self.serial_number}>"
