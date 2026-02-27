from __future__ import annotations

import os
import re
import threading
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union

import yaml
from xyzs_py.XLogs import XLogs

log = XLogs(__name__)


class ConfigError(RuntimeError):
    """配置错误（例如 required env 未提供、插值语法不合法等）"""


@dataclass(frozen=True)
class _Snapshot:
    """
    配置快照（copy-on-write）

    - data: 合并 + 插值后的最终配置 dict
    - files: 本次加载参与合并的 YAML 文件列表（便于排障）
    - dotenv_files: 本次尝试加载的 .env 文件列表（便于排障）
    """
    data: Dict[str, Any]
    files: Tuple[str, ...]
    dotenv_files: Tuple[str, ...]


class ConfigManager:
    """
    ConfigManager（静态全局配置）

    ✅ 满足你的 4 条要求：
    1) 只支持 YAML（.yml/.yaml）
    2) 程序初始化时通过 --config.path 加载多个 yaml（按顺序 overlay，后者覆盖前者）
    3) 不存在 --config.path 时默认加载 /config/config.yaml
    4) 保持 ConfigManager.get_str("a.b.c") 静态风格，不需要实例化

    ✅ 方案A（兼容 .env.local）：
    - 启动/重载时加载 .env / .env.local，把值注入 os.environ（或覆盖）
    - YAML 里支持 ${VAR} / ${VAR:default} / ${VAR:?error message} 字符串插值
    - 插值发生在“合并 YAML 之后”，保证读到的是最终值
    """

    _DEFAULT_PATH = "/config/config.yaml"
    _CLI_KEY_CONFIG_PATH = "config.path"

    # dotenv 文件名（你关心 .env.local，所以默认加载这两个）
    _DOTENV_BASE = ".env"
    _DOTENV_LOCAL = ".env.local"

    _lock = threading.Lock()
    _snapshot: Optional[_Snapshot] = None
    _loaded: bool = False
    _cli_files: Tuple[str, ...] = tuple()

    # ${VAR} / ${VAR:default} / ${VAR:?error}
    # 说明：
    # - name: 变量名（A-Z0-9_，也兼容小写，按你习惯）
    # - spec:
    #   - ":xxx" -> 默认值
    #   - ":?xxx" -> 必填错误提示
    _ENV_PATTERN = re.compile(r"\$\{(?P<name>[A-Za-z_][A-Za-z0-9_]*)"
                              r"(?P<spec>:(\?[^}]*)|:[^}]*)?\}")

    # 用于转义：如果你希望在配置里写字面量 "${...}"，可以写 "\${...}"
    _ESCAPED_MARK = "__CFG_ESC_DOLLAR_LBRACE__"

    # ========================= 启动 / 初始化 =========================

    @classmethod
    def run(cls, argv: Sequence[str]) -> None:
        """
        启动入口（建议 main() 最早调用一次）：
            ConfigManager.run(sys.argv[1:])

        - 解析 --config.path=path1,path2
        - 未提供则默认 /config/config.yaml
        - 强制构建新快照（reload=True）
        """
        files = cls._parse_cli_config_paths(argv)
        if not files:
            files = (cls._DEFAULT_PATH,)
        cls._cli_files = files
        cls._init(files=files, reload=True)

    @classmethod
    def init(cls) -> None:
        """
        懒加载入口：
        - 若未显式 run()，首次 get_xxx() 会触发 init()
        - init() 将使用 _cli_files 或默认 /config/config.yaml
        """
        if cls._loaded and cls._snapshot is not None:
            return
        files = cls._cli_files or (cls._DEFAULT_PATH,)
        cls._init(files=files, reload=False)

    @classmethod
    def reload(cls) -> None:
        """强制重载（重新加载 dotenv + YAML + 插值）"""
        files = cls._cli_files or (cls._DEFAULT_PATH,)
        cls._init(files=files, reload=True)

    # ========================= 读取 API（静态风格） =========================

    @classmethod
    def get(cls, key_path: str, default: Any = None) -> Any:
        cls.init()
        snap = cls._snapshot
        if snap is None:
            return default
        return cls._get_by_path(snap.data, key_path, default)

    @classmethod
    def contains(cls, key_path: str) -> bool:
        sentinel = object()
        return cls.get(key_path, sentinel) is not sentinel

    @classmethod
    def get_all(cls) -> Dict[str, Any]:
        cls.init()
        snap = cls._snapshot
        return dict(snap.data) if snap else {}

    @classmethod
    def get_str(cls, key_path: str, default: str = "") -> str:
        v = cls.get(key_path, None)
        if v is None:
            return default
        return v if isinstance(v, str) else str(v)

    @classmethod
    def get_int(cls, key_path: str, default: int = 0) -> int:
        v = cls.get(key_path, None)
        if v is None:
            return default
        try:
            return int(v)
        except (TypeError, ValueError):
            return default

    @classmethod
    def get_float(cls, key_path: str, default: float = 0.0) -> float:
        v = cls.get(key_path, None)
        if v is None:
            return default
        try:
            return float(v)
        except (TypeError, ValueError):
            return default

    @classmethod
    def get_bool(cls, key_path: str, default: bool = False) -> bool:
        v = cls.get(key_path, None)
        if v is None:
            return default
        if isinstance(v, bool):
            return v
        if isinstance(v, (int, float)):
            return v != 0
        if isinstance(v, str):
            s = v.strip().lower()
            if s in ("true", "1", "yes", "y", "on"):
                return True
            if s in ("false", "0", "no", "n", "off"):
                return False
            return default
        return bool(v)

    @classmethod
    def get_list(cls, key_path: str, default: Optional[List[Any]] = None) -> Optional[List[Any]]:
        v = cls.get(key_path, None)
        if isinstance(v, list):
            return v
        if isinstance(v, tuple):
            return list(v)
        if isinstance(v, str):
            parsed = cls._safe_parse_str(v)
            return parsed if isinstance(parsed, list) else default
        return default

    @classmethod
    def get_dict(cls, key_path: str, default: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        v = cls.get(key_path, None)
        if isinstance(v, dict):
            return v
        if isinstance(v, str):
            parsed = cls._safe_parse_str(v)
            return parsed if isinstance(parsed, dict) else default
        return default

    @classmethod
    def loaded_files(cls) -> Tuple[str, ...]:
        cls.init()
        return cls._snapshot.files if cls._snapshot else tuple()

    @classmethod
    def loaded_dotenv_files(cls) -> Tuple[str, ...]:
        cls.init()
        return cls._snapshot.dotenv_files if cls._snapshot else tuple()

    # ========================= 初始化实现（dotenv + yaml + interpolate） =========================

    @classmethod
    def _init(cls, files: Tuple[str, ...], reload: bool) -> None:
        if not reload and cls._loaded and cls._snapshot is not None:
            return

        with cls._lock:
            if not reload and cls._loaded and cls._snapshot is not None:
                return

            # 1) dotenv：把 .env / .env.local 注入到 os.environ
            dotenv_loaded = cls._load_dotenv(files)

            # 2) YAML：多文件按序 overlay，后者覆盖前者
            merged: Dict[str, Any] = {}
            loaded_yaml: List[str] = []

            for path in files:
                p = cls._normalize_path(path)
                data = cls._load_yaml_file(p)
                if data is None:
                    continue
                if not isinstance(data, dict):
                    log.info(f"[Config] YAML 顶层非 dict，已跳过：{p}")
                    continue
                cls._deep_merge_inplace(merged, data)
                loaded_yaml.append(p)

            # 3) 插值：将 merged 内所有字符串中的 ${VAR...} 替换为 env 值
            try:
                cls._interpolate_inplace(merged)
            except ConfigError as e:
                # 配置错误：这里选择抛出，让程序启动期尽早失败（更安全）
                raise

            cls._snapshot = _Snapshot(
                data=merged,
                files=tuple(loaded_yaml),
                dotenv_files=tuple(dotenv_loaded),
            )
            cls._loaded = True

            log.info(
                f"[Config] loaded yaml={len(loaded_yaml)} "
                f"({', '.join(loaded_yaml) if loaded_yaml else 'NONE'})"
            )
            if dotenv_loaded:
                log.info(f"[Config] loaded dotenv ({', '.join(dotenv_loaded)})")

    @classmethod
    def _load_dotenv(cls, yaml_files: Tuple[str, ...]) -> List[str]:
        """
        方案A：dotenv 只负责注入 os.environ，不直接 merge 到 config dict。

        加载策略（从低到高，后者覆盖前者）：
        1) config_dir/.env
        2) config_dir/.env.local
        3) cwd/.env
        4) cwd/.env.local

        说明：
        - 在容器/服务器部署时，常把配置挂载到 /config，因此优先加载 config_dir 是合理的
        - 本地开发时 cwd 下的 .env.local 可以覆盖 /config 中的 .env
        """
        candidates: List[str] = []

        config_dir = ""
        if yaml_files:
            first = cls._normalize_path(yaml_files[0])
            config_dir = os.path.dirname(first)

        def add_if_exists(p: str):
            if p and os.path.exists(p) and os.path.isfile(p):
                candidates.append(p)

        # config_dir
        if config_dir:
            add_if_exists(os.path.join(config_dir, cls._DOTENV_BASE))
            add_if_exists(os.path.join(config_dir, cls._DOTENV_LOCAL))

        # cwd
        cwd = os.getcwd()
        add_if_exists(os.path.join(cwd, cls._DOTENV_BASE))
        add_if_exists(os.path.join(cwd, cls._DOTENV_LOCAL))

        if not candidates:
            return []

        # 尝试使用 python-dotenv；不存在则降级：不报错，仅提示
        try:
            from dotenv import load_dotenv  # type: ignore
        except Exception:
            log.info("[Config] python-dotenv not installed, skip .env loading (os.environ only).")
            return []

        loaded: List[str] = []
        for p in candidates:
            # override=True：后加载的文件覆盖先加载的值，符合 overlay 直觉
            load_dotenv(p, override=True)
            loaded.append(p)
        return loaded

    # ========================= YAML 加载与 merge =========================

    @classmethod
    def _load_yaml_file(cls, path: str) -> Optional[Any]:
        try:
            if not os.path.exists(path) or not os.path.isfile(path):
                log.info(f"[Config] file not found, skip: {path}")
                return None
            with open(path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                return data if data is not None else {}
        except Exception as e:
            log.info(f"[Config] load yaml failed: {path}, err={e}")
            return None

    @classmethod
    def _deep_merge_inplace(cls, base: Dict[str, Any], inc: Dict[str, Any]) -> None:
        """
        深度合并规则：
        - dict + dict：递归 merge
        - list / 标量 / 类型不一致：整体覆盖（inc 覆盖 base）
        """
        for k, v in inc.items():
            if k in base and isinstance(base[k], dict) and isinstance(v, dict):
                cls._deep_merge_inplace(base[k], v)
            else:
                base[k] = v

    # ========================= 插值：${VAR} / ${VAR:default} / ${VAR:?error} =========================

    @classmethod
    def _interpolate_inplace(cls, node: Any) -> Any:
        """
        递归遍历 dict/list，遇到 str 才进行插值替换。
        - 原地修改，避免额外拷贝
        """
        if isinstance(node, dict):
            for k, v in list(node.items()):
                node[k] = cls._interpolate_inplace(v)
            return node

        if isinstance(node, list):
            for i in range(len(node)):
                node[i] = cls._interpolate_inplace(node[i])
            return node

        if isinstance(node, str):
            return cls._interpolate_str(node)

        return node

    @classmethod
    def _interpolate_str(cls, s: str) -> str:
        """
        对单个字符串做插值：
        - 支持多个占位符，例如 "postgres://${DB_USER}:${DB_PASS}@${DB_HOST}:${DB_PORT:5432}/x"
        - 支持必填校验：${OPENAI_API_KEY:?missing key}
        - 支持默认值：${REDIS_HOST:127.0.0.1}
        - 支持转义：\\${NOT_A_VAR} 保持字面量 ${NOT_A_VAR}
        """
        if not s:
            return s

        # 处理转义：把 "\${" 暂存成特殊标记，避免被当作变量
        s2 = s.replace(r"\${", cls._ESCAPED_MARK)

        def repl(m: re.Match) -> str:
            name = m.group("name")
            spec = m.group("spec")  # None / ":default" / ":?error..."

            raw = os.environ.get(name)

            if raw is not None:
                return raw

            # 无环境变量时，看 spec
            if not spec:
                # 没默认值、没必填：替换为空串（也可以选择保留原文本，这里更偏“可运行”）
                return ""

            # spec 以 ":" 开头
            body = spec[1:]  # 去掉冒号
            if body.startswith("?"):
                # 必填缺失
                msg = body[1:].strip() or f"missing env: {name}"
                raise ConfigError(f"[Config] required env missing: {name}, {msg}")

            # 默认值
            return body

        out = cls._ENV_PATTERN.sub(repl, s2)

        # 恢复转义字面量
        out = out.replace(cls._ESCAPED_MARK, "${")
        return out

    # ========================= CLI / path / get-by-path =========================

    @classmethod
    def _parse_cli_config_paths(cls, argv: Sequence[str]) -> Tuple[str, ...]:
        if not argv:
            return tuple()

        kv = {}
        for raw in argv:
            if not raw:
                continue
            s = raw.strip()
            if s.startswith("--"):
                s = s[2:]
            if "=" not in s:
                continue
            k, v = s.split("=", 1)
            kv[k.strip()] = v.strip()

        spec = kv.get(cls._CLI_KEY_CONFIG_PATH)
        if not spec:
            return tuple()

        parts = [p.strip() for p in spec.split(",") if p.strip()]
        return tuple(parts)

    @classmethod
    def _normalize_path(cls, path: str) -> str:
        p = (path or "").strip()
        if not p:
            return p
        p = os.path.expanduser(p)
        if not os.path.isabs(p):
            p = os.path.abspath(p)
        return p

    @classmethod
    def _get_by_path(cls, root: Any, key_path: str, default: Any) -> Any:
        if root is None or not key_path:
            return default

        cur: Any = root
        tokens = cls._tokenize_path(key_path)
        if not tokens:
            return default

        for t in tokens:
            if isinstance(t, str):
                if not isinstance(cur, dict) or t not in cur:
                    return default
                cur = cur.get(t)
            else:
                idx = t
                if not isinstance(cur, list) or idx < 0 or idx >= len(cur):
                    return default
                cur = cur[idx]

            if cur is None:
                return default

        return cur

    @classmethod
    def _tokenize_path(cls, key_path: str) -> List[Union[str, int]]:
        """
        "a.b[0].c" -> ["a","b",0,"c"]
        """
        s = key_path.strip()
        out: List[Union[str, int]] = []
        buf: List[str] = []
        i, n = 0, len(s)

        def flush():
            if buf:
                out.append("".join(buf))
                buf.clear()

        while i < n:
            ch = s[i]
            if ch == ".":
                flush()
                i += 1
                continue
            if ch == "[":
                flush()
                j = s.find("]", i + 1)
                if j == -1:
                    return []
                idx_str = s[i + 1:j].strip()
                if not idx_str.isdigit():
                    return []
                out.append(int(idx_str))
                i = j + 1
                continue

            buf.append(ch)
            i += 1

        flush()
        return out

    @classmethod
    def _safe_parse_str(cls, s: str) -> Any:
        if not isinstance(s, str):
            return None
        ss = s.strip()
        if not ss:
            return None
        try:
            return yaml.safe_load(ss)
        except Exception:
            return None
