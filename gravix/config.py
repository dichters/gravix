import os
from dataclasses import dataclass
from pathlib import Path

import yaml
from loguru import logger as log


# Config keys and their corresponding environment variables
_CONFIG_ENV_MAP = {
    "work_dir": "GRAVIX_WORK_DIR",
    "lite_base_url": "GRAVIX_LITE_BASE_URL",
    "lite_sk": "GRAVIX_LITE_SK",
    "full_base_url": "GRAVIX_FULL_BASE_URL",
    "full_sk": "GRAVIX_FULL_SK",
}

DEFAULT_CONFIG_FILE = "gravix_conf.yaml"


@dataclass
class GravixConfig:
    work_dir: str
    lite_base_url: str
    lite_sk: str
    full_base_url: str
    full_sk: str


def _read_config_file(path: str | Path) -> dict:
    p = Path(path)
    if not p.exists():
        log.info("Config file not found: {}", p)
        return {}
    with open(p, "r") as f:
        data = yaml.safe_load(f)
    return data if isinstance(data, dict) else {}


def load_config(config_file: str | Path | None = None) -> GravixConfig:
    if config_file is None:
        config_file = DEFAULT_CONFIG_FILE

    file_values = _read_config_file(config_file)

    resolved = {}
    missing = []
    for key, env_var in _CONFIG_ENV_MAP.items():
        env_val = os.environ.get(env_var)
        if env_val is not None:
            resolved[key] = env_val
        elif key in file_values and file_values[key] is not None:
            resolved[key] = str(file_values[key])
        else:
            missing.append(key)

    if missing:
        hints = [f"  {k}: set env {_CONFIG_ENV_MAP[k]} or add to {config_file}" for k in missing]
        log.error(f"Missing required config: {', '.join(missing)}")
        log.error(f"Fix by:\n{'\n'.join(hints)}")
        raise SystemExit(1)

    log.info("Config loaded from: {}", config_file)
    return GravixConfig(**resolved)
