import yaml

from xyzs_py.XLogs import XLogs

# 初始化日志
log = XLogs(__name__)


class XConfig:
    default_config = None
    env_config = None

    @staticmethod
    def init(base_path, env='config'):
        """
        初始化配置管理器并加载默认配置文件及环境特定的配置文件。

        参数:
        default_path (str): 默认配置文件的路径。
        env_path (str): 环境特定配置文件的路径，可选。
        """
        XConfig.default_config = XConfig.__load_config(f"{base_path}/config.yaml")
        XConfig.env_config = XConfig.__load_config(f"{base_path}/{env}.yaml")

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
            with open(path, 'r') as file:
                return yaml.safe_load(file) or {}
        except FileNotFoundError:
            log.info(f"错误：未找到配置文件 {path}。")
            return {}
        except yaml.YAMLError as e:
            print(f"解析 YAML 文件错误: {e}")
            return {}

    @staticmethod
    def get(key_path, default=''):
        """
        使用点分隔的键路径从配置中检索值，首先检查环境配置，如果未找到，则检查默认配置。

        参数:
        key_path (str): 配置项的点分隔路径。
        default (any): 如果未找到键，则返回的默认值。

        返回:
        any: 配置中的值或默认值。
        """
        value = XConfig.__retrieve_value(XConfig.env_config, key_path)
        if value is None:  # 如果环境配置中没有找到，回退到默认配置
            value = XConfig.__retrieve_value(XConfig.default_config, key_path)

        return value if value is not None else default

    @staticmethod
    def __retrieve_value(config, key_path):
        """
        从给定配置中按照键路径检索值。

        参数:
        config (dict): 配置字典。
        key_path (str): 配置项的点分隔路径。

        返回:
        any: 检索到的值，如果未找到返回 None。
        """
        if config is None:
            return None
        keys = key_path.split('.')
        value = config
        for key in keys:
            value = value.get(key)
            if value is None:
                return None
        return value
