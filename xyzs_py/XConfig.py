from typing import Any, Optional, Dict, List

import yaml
import os
from xyzs_py.XLogs import XLogs

log = XLogs(__name__)


class XConfig:
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

    def get_list(self, key: str, default: Optional[List[Any]] = None) -> Optional[List[Any]]:
        """
        获取 list 配置。

        支持：
        - 原生 list（YAML 中直接写 - a / [a,b]）
        - 字符串形式的 YAML/JSON list（如 "[1,2]" / "['a','b']" / "- a\\n- b"）
        - 可选：逗号分隔字符串 "a,b,c" -> ["a","b","c"]
        """
        value = self.get(key, default)

        # 1) 原生 list 直接返回
        if isinstance(value, list):
            return value

        # 2) tuple 等可迭代容器（可选支持）
        if isinstance(value, tuple):
            return list(value)

        # 3) 字符串：尝试安全解析成 list
        if isinstance(value, str):
            parsed = self._safe_parse_container_str(value)
            if isinstance(parsed, list):
                return parsed

            # 4) 兜底：支持 "a,b,c" 这种写法（你不需要可删）
            if "," in value:
                parts = [p.strip() for p in value.split(",") if p.strip()]
                return parts if parts else default

        return default

    def get_dict(self, key: str, default: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """
        获取 dict 配置。

        支持：
        - 原生 dict（YAML 中直接写 key: value 或 {a:1}）
        - 字符串形式的 YAML/JSON dict（如 "{a: 1}" / '{"a":1}' / "a: 1\\nb: 2"）
        """
        value = self.get(key, default)

        # 1) 原生 dict 直接返回
        if isinstance(value, dict):
            return value

        # 2) 字符串：尝试安全解析成 dict
        if isinstance(value, str):
            parsed = self._safe_parse_container_str(value)
            if isinstance(parsed, dict):
                return parsed

        return default

    def _safe_parse_container_str(self, s: str) -> Any:
        """
        安全解析“可能是容器（list/dict）”的字符串。

        解析策略：
        - 使用 yaml.safe_load：可解析 YAML/JSON 子集（比 json.loads 更宽容）
        - 解析失败返回 None
        """
        if not isinstance(s, str):
            return None
        s = s.strip()
        if not s:
            return None
        try:
            return yaml.safe_load(s)
        except Exception:
            return None
