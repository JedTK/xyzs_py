import json
import re

class JsonUtil:
    @staticmethod
    def get(data: dict, key_path: str, default=None):
        """
        通用方法：根据点分路径获取值，例如 'user.info.name'

        :param data: 原始JSON字典
        :param key_path: 点分路径（支持嵌套）
        :param default: 默认值
        :return: 对应值或默认值
        """
        if not isinstance(data, dict) or not key_path:
            return default
        keys = key_path.split('.')
        current = data
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return default
        return current

    @staticmethod
    def get_str(data: dict, key_path: str, default='') -> str:
        try:
            val = JsonUtil.get(data, key_path, default)
            return str(val) if val is not None else default
        except Exception:
            return default

    @staticmethod
    def get_int(data: dict, key_path: str, default=0) -> int:
        try:
            return int(JsonUtil.get(data, key_path, default))
        except (ValueError, TypeError):
            return default

    @staticmethod
    def get_float(data: dict, key_path: str, default=0.0) -> float:
        try:
            return float(JsonUtil.get(data, key_path, default))
        except (ValueError, TypeError):
            return default

    @staticmethod
    def get_bool(data: dict, key_path: str, default=False) -> bool:
        value = JsonUtil.get(data, key_path, default)
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.strip().lower() in ['true', '1', 'yes', 'y']
        return bool(value)

    @staticmethod
    def get_list(data: dict, key_path: str, default=None) -> list:
        value = JsonUtil.get(data, key_path, default)
        if isinstance(value, list):
            return value
        try:
            return eval(value) if isinstance(value, str) else default
        except Exception:
            return default or []

    @staticmethod
    def get_dict(data: dict, key_path: str, default=None) -> dict:
        value = JsonUtil.get(data, key_path, default)
        if isinstance(value, dict):
            return value
        try:
            return eval(value) if isinstance(value, str) else default
        except Exception:
            return default or {}

    @staticmethod
    def parse_json(json_text: str) -> dict:
        """
        将JSON字符串解析为字典对象。
        :param json_text: 原始JSON字符串
        :return: 字典对象或空字典
        """
        try:
            return json.loads(json_text)
        except json.JSONDecodeError:
            return {}

    @staticmethod
    def json_format_clear(text: str) -> str:
        """
        清洗翻译或接口返回的文本，去除 `json`、反引号等 Markdown 包裹，只保留有效 JSON 数据。
        如果内容中嵌套 markdown 或多余说明，则尽可能提取合法 JSON 部分。

        :param text: 待清洗文本
        :return: 清洗后的 JSON 字符串
        """
        import json

        if not text:
            return ""

        # 1. 去除 markdown 包裹的前缀和后缀
        text = re.sub(r"^\s*```(?:json)?\s*", "", text, flags=re.IGNORECASE)
        text = re.sub(r"\s*```$", "", text.strip(), flags=re.IGNORECASE)

        # 2. 去除前后空行
        text = text.strip()

        # 3. 如果本身就是合法的 JSON，直接返回
        try:
            json.loads(text)
            return text
        except json.JSONDecodeError:
            pass  # 继续尝试清洗

        # 4. 尝试提取 JSON 数组（优先处理列表结构）
        match_array = re.search(r"(\[\s*\{.*\}\s*\])", text, flags=re.DOTALL)
        if match_array:
            candidate = match_array.group(1).strip()
            try:
                json.loads(candidate)
                return candidate
            except json.JSONDecodeError:
                pass

        # 5. 尝试提取 JSON 对象
        match_object = re.search(r"(\{\s*.*\s*\})", text, flags=re.DOTALL)
        if match_object:
            candidate = match_object.group(1).strip()
            try:
                json.loads(candidate)
                return candidate
            except json.JSONDecodeError:
                pass

        # 6. 最终失败，返回原始文本（但已去除 markdown 包裹）
        return text
