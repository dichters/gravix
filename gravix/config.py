import json
import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv
from loguru import logger as log


DEFAULT_CONFIG_FILE = "gravix_conf.json"
DEFAULT_WORK_DIR = ".gravix"

# Sensitive config keys (API keys only) and their environment variable names
_KEY_ENV_MAP = {
    "lite_key": "GRAVIX_LITE_KEY",
    "full_key": "GRAVIX_FULL_KEY",
}

# Required llm fields and their dotted path for error messages
_REQUIRED_LLM_FIELDS = {
    "llm.lite.base_url": ("lite", "base_url"),
    "llm.lite.model": ("lite", "model"),
    "llm.full.base_url": ("full", "base_url"),
    "llm.full.model": ("full", "model"),
}


@dataclass
class GravixConfig:
    """Configuration for gravix.

    Attributes:
        work_dir: gravix workspace directory (from json or default)
        lite_base_url: Lite LLM API base URL (from json)
        lite_model: Lite LLM model name (from json)
        lite_key: Lite LLM API key (from env)
        full_base_url: Full LLM API base URL (from json)
        full_model: Full LLM model name (from json)
        full_key: Full LLM API key (from env)
    """

    work_dir: str = field(default=DEFAULT_WORK_DIR)
    lite_base_url: str = field(default="")
    lite_model: str = field(default="")
    lite_key: str = field(default="")
    full_base_url: str = field(default="")
    full_model: str = field(default="")
    full_key: str = field(default="")


def _load_env_keys() -> dict[str, str]:
    # Load .env from current working directory
    # System environment variables take priority (override=False is default)
    load_dotenv(".env")

    result = {}
    for key, env_var in _KEY_ENV_MAP.items():
        val = os.environ.get(env_var)
        if val is not None:
            result[key] = val
    return result


def _read_config_file(path: str | Path) -> dict:
    """Read JSON config file."""
    p = Path(path)
    if not p.exists():
        log.debug("Config file not found: {}", p)
        return {}
    try:
        with open(p, "r") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        log.error("Invalid JSON in config file {}: {}", p, e)
        raise SystemExit(1)
    return data if isinstance(data, dict) else {}


def _extract_llm_fields(file_values: dict) -> dict[str, str]:
    """Extract required llm fields from config values."""
    result = {}
    llm = file_values.get("llm", {}) or {}
    for dotted_path, (section, field_name) in _REQUIRED_LLM_FIELDS.items():
        section_data = llm.get(section, {}) or {}
        result[dotted_path] = str(section_data.get(field_name, "")).strip()
    return result


def load_config(config_file: str | Path | None = None) -> GravixConfig:
    """Load gravix configuration.

    Config sources:
    - work_dir: from json file, defaults to '.gravix' if not specified
    - llm base_url and model: from json file (llm.lite / llm.full sections)
    - LLM API keys: from environment variables or .env file

    Args:
        config_file: Path to json config file. Defaults to 'gravix_conf.json'.

    Returns:
        GravixConfig instance.

    Raises:
        SystemExit: If required config fields or API keys are missing.
    """
    if config_file is None:
        config_file = DEFAULT_CONFIG_FILE

    # Read json config for business settings
    file_values = _read_config_file(config_file)

    # Extract and validate required llm fields from json
    llm_fields = _extract_llm_fields(file_values)
    missing_fields = [k for k, v in llm_fields.items() if not v]
    if missing_fields:
        log.error(
            "Missing required llm config in {}: {}",
            config_file,
            ", ".join(missing_fields),
        )
        raise SystemExit(1)

    # Load API keys from env (system env or .env file)
    env_keys = _load_env_keys()

    # Check for missing required API keys
    missing_keys = []
    for key in _KEY_ENV_MAP:
        if key not in env_keys or not env_keys[key]:
            missing_keys.append(key)

    if missing_keys:
        hints = [
            f"  {k}: set env {_KEY_ENV_MAP[k]} or add to .env"
            for k in missing_keys
        ]
        log.error("Missing required LLM API keys: {}", ", ".join(missing_keys))
        log.error("Fix by:\n{}", "\n".join(hints))
        raise SystemExit(1)

    # Build config
    work_dir = file_values.get("work_dir", DEFAULT_WORK_DIR)

    config = GravixConfig(
        work_dir=str(work_dir),
        lite_base_url=llm_fields["llm.lite.base_url"],
        lite_model=llm_fields["llm.lite.model"],
        lite_key=env_keys["lite_key"],
        full_base_url=llm_fields["llm.full.base_url"],
        full_model=llm_fields["llm.full.model"],
        full_key=env_keys["full_key"],
    )

    log.info("Config loaded from: {} and environment", config_file)
    return config
