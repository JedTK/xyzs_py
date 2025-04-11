import yaml
from xyzs_py.XLogs import XLogs

# 初始化日志
log = XLogs(__name__)


class XConfig:
    default_config = None
    config_data = None
    base_path = None  # 存储基本路径
    env = None  # 存储环境名称

    @staticmethod
    def init(base_path: str, env='config'):
        """
        初始化配置管理器并加载默认配置文件及环境特定的配置文件。

        参数:
        base_path (str): 配置文件的路径。
        env (str): 环境特定配置文件的名称，可选。
        """
        XConfig.base_path = base_path  # 记录基本路径
        XConfig.env = env  # 记录环境名称
        XConfig.default_config = XConfig.__load_config(f"{base_path}/config.yaml")
        XConfig.config_data = XConfig.__load_config(f"{base_path}/{env}.yaml")

    @staticmethod
    def __load_config(path):
        """
        加载 YAML 配置文件。

        参数:
        path (str): 配置文件的路径。

        返回:
        dict: 加载的配置字典。
        """
        try:
            with open(path, 'r', encoding='utf-8') as file:
                return yaml.safe_load(file) or {}
        except FileNotFoundError:
            log.info(f"错误：未找到配置文件 {path}。")
            return {}
        except yaml.YAMLError as e:
            print(f"解析 YAML 文件错误: {e}")
            return {}

    @staticmethod
    def get(key_path, default=None):
        """
        使用点分隔的键路径从配置中检索值，首先检查环境配置，如果未找到，则检查默认配置。

        参数:
        key_path (str): 配置项的点分隔路径。
        default (any): 如果未找到键，则返回的默认值。

        返回:
        any: 配置中的值或默认值。
        """
        value = XConfig.__retrieve_value(XConfig.config_data, key_path, default)
        if value is None:  # 如果环境配置中没有找到，回退到默认配置
            value = XConfig.__retrieve_value(XConfig.default_config, key_path, default)
        return value if value is not None else default

    @staticmethod
    def __retrieve_value(config, key_path, default=None):
        """
        从给定配置中按照键路径检索值。

        参数:
        config (dict): 配置字典。
        key_path (str): 配置项的点分隔路径。

        返回:
        any: 检索到的值，如果未找到返回 None。
        """
        if config is None:
            return default
        keys = key_path.split('.')
        value = config
        for key in keys:
            value = value.get(key)
            if value is None:
                return default
        return value

    @staticmethod
    def set(key_path, value, env='config'):
        """
        设置指定键路径的值，并保存到对应的 YAML 文件。

        参数:
        key_path (str): 配置项的点分隔路径。
        value (any): 要设置的新值。
        env (str): 指定修改哪个配置，'default' 表示默认配置，'config' 表示环境配置。
        """
        # 根据 env 决定修改哪个配置
        if env == 'default':
            config = XConfig.default_config
            path = f"{XConfig.base_path}/config.yaml"
        else:
            config = XConfig.config_data
            path = f"{XConfig.base_path}/{XConfig.env}.yaml"

        # 更新配置字典
        XConfig.__update_value(config, key_path, value)
        # 保存到文件
        XConfig.__save_config(config, path)

    @staticmethod
    def __update_value(config, key_path, value):
        """
        更新配置字典中指定键路径的值。

        参数:
        config (dict): 配置字典。
        key_path (str): 配置项的点分隔路径。
        value (any): 要设置的新值。
        """
        keys = key_path.split('.')
        current = config
        # 逐级定位到目标键的前一级
        for key in keys[:-1]:
            current = current.setdefault(key, {})  # 如果键不存在，创建空字典
        # 设置最终的值
        current[keys[-1]] = value

    @staticmethod
    def __save_config(config, path):
        """
        将配置字典保存到 YAML 文件。

        参数:
        config (dict): 配置字典。
        path (str): YAML 文件路径。
        """
        with open(path, 'w', encoding='utf-8') as file:
            yaml.dump(config, file, allow_unicode=True)

    @staticmethod
    def get_str(key, default=''):
        """获取字符串类型的值"""
        return str(XConfig.get(key, default))

    @staticmethod
    def get_int(key, default=0):
        """获取整数类型的值"""
        try:
            return int(XConfig.get(key, default))
        except ValueError:
            return default

    @staticmethod
    def get_float(key, default=0.0):
        """获取浮点数类型的值"""
        try:
            return float(XConfig.get(key, default))
        except ValueError:
            return default

    @staticmethod
    def get_bool(key, default=False):
        """获取布尔类型的值"""
        value = XConfig.get(key, default)
        if isinstance(value, str):
            return value.lower() in ['true', '1', 'yes', 'y']
        return bool(value)

    @staticmethod
    def get_list(key, default=None):
        """获取列表类型的值"""
        value = XConfig.get(key, default)
        if isinstance(value, list):
            return value
        try:
            return eval(value) if isinstance(value, str) else default
        except Exception:
            return default

    @staticmethod
    def get_dict(key, default=None):
        """获取字典类型的值"""
        value = XConfig.get(key, default)
        if isinstance(value, dict):
            return value
        try:
            return eval(value) if isinstance(value, str) else default
        except Exception:
            return default
