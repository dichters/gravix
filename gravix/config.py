import os
from dataclasses import dataclass, field
from pathlib import Path

import yaml
from dotenv import load_dotenv
from loguru import logger as log


DEFAULT_CONFIG_FILE = "gravix_conf.yaml"
DEFAULT_WORK_DIR = ".gravix"

# Sensitive config keys and their environment variable names
_SYS_ENV_MAP = {
    "lite_base_url": "GRAVIX_LITE_BASE_URL",
    "lite_key": "GRAVIX_LITE_KEY",
    "full_base_url": "GRAVIX_FULL_BASE_URL",
    "full_key": "GRAVIX_FULL_KEY",
}


@dataclass
class GravixConfig:
    """Configuration for gravix.

    Attributes:
        work_dir: gravix workspace directory (from yaml or default)
        lite_base_url: Lite LLM API base URL (from env)
        lite_key: Lite LLM API key (from env)
        full_base_url: Full LLM API base URL (from env)
        full_key: Full LLM API key (from env)
    """

    work_dir: str = field(default=DEFAULT_WORK_DIR)
    lite_base_url: str = field(default="")
    lite_key: str = field(default="")
    full_base_url: str = field(default="")
    full_key: str = field(default="")


def _load_env_values() -> dict[str, str]:
    # Load .env from current working directory
    # System environment variables take priority (override=False is default)
    load_dotenv(".env")

    result = {}
    for key, env_var in _SYS_ENV_MAP.items():
        val = os.environ.get(env_var)
        if val is not None:
            result[key] = val
    return result


def _read_config_file(path: str | Path) -> dict:
    """Read YAML config file."""
    p = Path(path)
    if not p.exists():
        log.debug("Config file not found: {}", p)
        return {}
    with open(p, "r") as f:
        data = yaml.safe_load(f)
    return data if isinstance(data, dict) else {}


def load_config(config_file: str | Path | None = None) -> GravixConfig:
    """Load gravix configuration.

    Config sources:
    - work_dir: from yaml file, defaults to '.gravix' if not specified
    - LLM credentials (base_url/key): from environment variables or .env file

    Args:
        config_file: Path to yaml config file. Defaults to 'gravix_conf.yaml'.

    Returns:
        GravixConfig instance.

    Raises:
        SystemExit: If required LLM credentials are missing.
    """
    if config_file is None:
        config_file = DEFAULT_CONFIG_FILE

    # Read yaml config for business settings
    file_values = _read_config_file(config_file)

    # Load sensitive values from env (system env or .env file)
    env_values = _load_env_values()

    # Check for missing required sensitive configs
    missing = []
    for key in _SYS_ENV_MAP:
        if key not in env_values or not env_values[key]:
            missing.append(key)

    if missing:
        hints = [
            f"  {k}: set env {_SYS_ENV_MAP[k]} or add to .env"
            for k in missing
        ]
        log.error("Missing required LLM credentials: {}", ", ".join(missing))
        log.error("Fix by:\n{}", "\n".join(hints))
        raise SystemExit(1)

    # Build config
    work_dir = file_values.get("work_dir", DEFAULT_WORK_DIR)

    config = GravixConfig(
        work_dir=str(work_dir),
        lite_base_url=env_values["lite_base_url"],
        lite_key=env_values["lite_key"],
        full_base_url=env_values["full_base_url"],
        full_key=env_values["full_key"],
    )

    log.info("Config loaded from: {} and environment", config_file)
    return config
