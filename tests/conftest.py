import os
from collections.abc import Generator
from pathlib import Path

import pytest
import yaml


def write_config(
    path: Path,
    *,
    work_dir: str = ".gravix",
    lite_base_url: str = "https://api.lite.example.com/v1",
    lite_model: str = "gpt-4o-mini",
    full_base_url: str = "https://api.full.example.com/v1",
    full_model: str = "gpt-4o",
) -> None:
    """Create a gravix_conf.yaml with test values."""
    data = {
        "work_dir": work_dir,
        "llm": {
            "lite": {
                "base_url": lite_base_url,
                "model": lite_model,
            },
            "full": {
                "base_url": full_base_url,
                "model": full_model,
            },
        },
    }
    with open(path, "w") as f:
        yaml.dump(data, f)


def write_config_missing_llm(
    path: Path,
    *,
    work_dir: str = ".gravix",
    llm: dict | None = None,
) -> None:
    """Create a gravix_conf.yaml with partial or missing llm config."""
    data: dict = {"work_dir": work_dir}
    if llm is not None:
        data["llm"] = llm
    with open(path, "w") as f:
        yaml.dump(data, f)


def write_env_file(
    path: Path,
    *,
    lite_key: str = "sk-lite-test",
    full_key: str = "sk-full-test",
) -> None:
    """Create a .env file with test values for LLM API keys."""
    lines = [
        f"GRAVIX_LITE_KEY={lite_key}",
        f"GRAVIX_FULL_KEY={full_key}",
    ]
    with open(path, "w") as f:
        f.write("\n".join(lines) + "\n")


def clear_gravix_env() -> None:
    """Clear all gravix-related environment variables."""
    env_keys = [
        "GRAVIX_LITE_KEY",
        "GRAVIX_FULL_KEY",
    ]
    for key in env_keys:
        os.environ.pop(key, None)


@pytest.fixture
def tmp_workdir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Change working directory to tmp_path for test isolation."""
    # Clear any existing gravix env vars
    clear_gravix_env()
    monkeypatch.chdir(tmp_path)
    return tmp_path
