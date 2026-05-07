import os
import subprocess
import sys
from pathlib import Path

import pytest

from tests.conftest import write_config


def _run_gravix(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "gravix.cli"] + args,
        capture_output=True,
        text=True,
    )


class TestCliInit:
    """CLI gravix init integration tests."""

    def test_init_with_default_config(self, tmp_workdir: Path) -> None:
        write_config(tmp_workdir / "gravix_conf.yaml")
        result = _run_gravix(["init"])
        assert result.returncode == 0
        assert (tmp_workdir / ".gravix").is_dir()
        assert (tmp_workdir / ".gravix" / "graph.lbug").exists()
        assert (tmp_workdir / ".gravix" / "abstract.db").exists()
        assert (tmp_workdir / ".gravix" / "raw").is_dir()

    def test_init_with_custom_config(self, tmp_workdir: Path) -> None:
        custom = tmp_workdir / "custom.yaml"
        write_config(custom, work_dir=".custom_dir")
        result = _run_gravix(["init", "-conf", str(custom)])
        assert result.returncode == 0
        assert (tmp_workdir / ".custom_dir").is_dir()

    def test_init_with_env_vars(self, tmp_workdir: Path) -> None:
        env = {
            "GRAVIX_WORK_DIR": ".env_gravix",
            "GRAVIX_LITE_BASE_URL": "https://a.com/v1",
            "GRAVIX_LITE_SK": "sk1",
            "GRAVIX_FULL_BASE_URL": "https://b.com/v1",
            "GRAVIX_FULL_SK": "sk2",
        }
        full_env = {**os.environ, **env}
        result = subprocess.run(
            [sys.executable, "-m", "gravix.cli", "init"],
            capture_output=True,
            text=True,
            env=full_env,
        )
        assert result.returncode == 0
        assert (tmp_workdir / ".env_gravix").is_dir()

    def test_init_missing_config_exits(self, tmp_workdir: Path) -> None:
        result = _run_gravix(["init"])
        assert result.returncode == 1

    def test_init_absolute_work_dir(self, tmp_workdir: Path) -> None:
        abs_dir = tmp_workdir / "absolute_workspace"
        write_config(tmp_workdir / "gravix_conf.yaml", work_dir=str(abs_dir))
        result = _run_gravix(["init"])
        assert result.returncode == 0
        assert abs_dir.is_dir()
        assert (abs_dir / "graph.lbug").exists()

    def test_init_idempotent(self, tmp_workdir: Path) -> None:
        write_config(tmp_workdir / "gravix_conf.yaml")
        _run_gravix(["init"])
        result = _run_gravix(["init"])
        assert result.returncode == 0
        assert (tmp_workdir / ".gravix" / "graph.lbug").exists()
        assert (tmp_workdir / ".gravix" / "abstract.db").exists()
        assert (tmp_workdir / ".gravix" / "raw").is_dir()
