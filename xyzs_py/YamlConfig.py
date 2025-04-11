import yaml
import os
from xyzs_py.XLogs import XLogs

log = XLogs(__name__)


class YamlConfig:
    def __init__(self, file_path: str):
        """
        初始化 YamlConfig 实例，绑定指定的 YAML 文件。
        :param file_path: YAML 文件路径
        """
        self.file_path = file_path
        self.config = self.__load()

    def __load(self) -> dict:
        """
        加载 YAML 配置。
        """
        if not os.path.exists(self.file_path):
            log.info(f"未找到配置文件：{self.file_path}，将使用空配置。")
            return {}
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f) or {}
        except yaml.YAMLError as e:
            log.info(f"解析 YAML 文件失败：{e}")
            return {}

    def get(self, key_path: str, default=None):
        return self.__retrieve_value(self.config, key_path, default)

    def set(self, key_path: str, value):
        self.__update_value(self.config, key_path, value)

    def save(self):
        with open(self.file_path, 'w', encoding='utf-8') as f:
            yaml.dump(self.config, f, allow_unicode=True)

    def __retrieve_value(self, config, key_path, default=None):
        if config is None:
            return default
        keys = key_path.split('.')
        value = config
        for key in keys:
            if not isinstance(value, dict):
                return default
            value = value.get(key)
            if value is None:
                return default
        return value

    def __update_value(self, config, key_path, value):
        keys = key_path.split('.')
        current = config
        for key in keys[:-1]:
            current = current.setdefault(key, {})
        current[keys[-1]] = value

    # 类型辅助方法
    def get_str(self, key, default=''):
        return str(self.get(key, default))

    def get_int(self, key, default=0):
        try:
            return int(self.get(key, default))
        except (ValueError, TypeError):
            return default

    def get_float(self, key, default=0.0):
        try:
            return float(self.get(key, default))
        except (ValueError, TypeError):
            return default

    def get_bool(self, key, default=False):
        value = self.get(key, default)
        if isinstance(value, str):
            return value.lower() in ['true', '1', 'yes']
        return bool(value)

    def get_list(self, key, default=None):
        value = self.get(key, default)
        if isinstance(value, list):
            return value
        try:
            return eval(value) if isinstance(value, str) else default
        except Exception:
            return default

    def get_dict(self, key, default=None):
        value = self.get(key, default)
        if isinstance(value, dict):
            return value
        try:
            return eval(value) if isinstance(value, str) else default
        except Exception:
            return default
