import os
from collections.abc import Generator
from pathlib import Path

import pytest
import yaml


def write_config(
    path: Path,
    *,
    work_dir: str = ".gravix",
) -> None:
    """Create a gravix_conf.yaml with test values."""
    data = {
        "work_dir": work_dir,
    }
    with open(path, "w") as f:
        yaml.dump(data, f)


def write_env_file(
    path: Path,
    *,
    lite_base_url: str = "https://api.lite.example.com/v1",
    lite_key: str = "sk-lite-test",
    full_base_url: str = "https://api.full.example.com/v1",
    full_key: str = "sk-full-test",
) -> None:
    """Create a .env file with test values for LLM credentials."""
    lines = [
        f"GRAVIX_LITE_BASE_URL={lite_base_url}",
        f"GRAVIX_LITE_KEY={lite_key}",
        f"GRAVIX_FULL_BASE_URL={full_base_url}",
        f"GRAVIX_FULL_KEY={full_key}",
    ]
    with open(path, "w") as f:
        f.write("\n".join(lines) + "\n")


def clear_gravix_env() -> None:
    """Clear all gravix-related environment variables."""
    env_keys = [
        "GRAVIX_LITE_BASE_URL",
        "GRAVIX_LITE_KEY",
        "GRAVIX_FULL_BASE_URL",
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
