import os
from collections.abc import Generator
from pathlib import Path

import pytest


@pytest.fixture
def tmp_workdir(tmp_path: Path) -> Generator[Path, None, None]:
    prev = Path.cwd()
    os.chdir(tmp_path)
    yield tmp_path
    os.chdir(prev)


def write_config(path: Path, **overrides: str) -> Path:
    import yaml

    defaults = {
        "work_dir": ".gravix",
        "lite_base_url": "https://api.lite.example.com/v1",
        "lite_sk": "sk-lite-test",
        "full_base_url": "https://api.full.example.com/v1",
        "full_sk": "sk-full-test",
    }
    defaults.update(overrides)
    with open(path, "w") as f:
        yaml.dump(defaults, f)
    return path
