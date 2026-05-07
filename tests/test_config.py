import os
from collections.abc import Generator
from pathlib import Path

import pytest

from gravix.config import load_config
from tests.conftest import write_config


class TestLoadConfigFromFile:
    """Config is read from a YAML file."""

    def test_load_all_from_config_file(self, tmp_workdir: Path) -> None:
        write_config(tmp_workdir / "gravix_conf.yaml")
        cfg = load_config()
        assert cfg.work_dir == ".gravix"
        assert cfg.lite_base_url == "https://api.lite.example.com/v1"
        assert cfg.lite_sk == "sk-lite-test"
        assert cfg.full_base_url == "https://api.full.example.com/v1"
        assert cfg.full_sk == "sk-full-test"

    def test_load_from_custom_config_file(self, tmp_workdir: Path) -> None:
        custom = tmp_workdir / "my_conf.yaml"
        write_config(custom, work_dir=".custom")
        cfg = load_config(config_file=str(custom))
        assert cfg.work_dir == ".custom"

    def test_missing_config_file_and_no_env(self, tmp_workdir: Path) -> None:
        # No config file, no env vars => error
        with pytest.raises(SystemExit, match="1"):
            load_config()


class TestLoadConfigFromEnv:
    """Config is read from environment variables."""

    ENV_MAP = {
        "GRAVIX_WORK_DIR": ".env_gravix",
        "GRAVIX_LITE_BASE_URL": "https://env.lite.example.com/v1",
        "GRAVIX_LITE_SK": "sk-env-lite",
        "GRAVIX_FULL_BASE_URL": "https://env.full.example.com/v1",
        "GRAVIX_FULL_SK": "sk-env-full",
    }

    @pytest.fixture(autouse=True)
    def set_env(self) -> Generator[None, None, None]:
        for k, v in self.ENV_MAP.items():
            os.environ[k] = v
        yield
        for k in self.ENV_MAP:
            os.environ.pop(k, None)

    def test_load_all_from_env(self, tmp_workdir: Path) -> None:
        cfg = load_config()
        assert cfg.work_dir == ".env_gravix"
        assert cfg.lite_base_url == "https://env.lite.example.com/v1"
        assert cfg.lite_sk == "sk-env-lite"
        assert cfg.full_base_url == "https://env.full.example.com/v1"
        assert cfg.full_sk == "sk-env-full"


class TestEnvOverridesFile:
    """Environment variables take priority over config file."""

    ENV_MAP = {
        "GRAVIX_WORK_DIR": ".env_override",
        "GRAVIX_LITE_BASE_URL": "https://override.lite.example.com/v1",
        "GRAVIX_LITE_SK": "sk-override-lite",
        "GRAVIX_FULL_BASE_URL": "https://override.full.example.com/v1",
        "GRAVIX_FULL_SK": "sk-override-full",
    }

    @pytest.fixture(autouse=True)
    def set_env(self) -> Generator[None, None, None]:
        for k, v in self.ENV_MAP.items():
            os.environ[k] = v
        yield
        for k in self.ENV_MAP:
            os.environ.pop(k, None)

    def test_env_overrides_file(self, tmp_workdir: Path) -> None:
        write_config(tmp_workdir / "gravix_conf.yaml", work_dir=".file_gravix")
        cfg = load_config()
        assert cfg.work_dir == ".env_override"
        assert cfg.lite_base_url == "https://override.lite.example.com/v1"


class TestPartialConfig:
    """Some keys from env, rest from file."""

    def test_partial_env_and_file(self, tmp_workdir: Path) -> None:
        write_config(tmp_workdir / "gravix_conf.yaml")
        os.environ["GRAVIX_WORK_DIR"] = ".partial_env"
        try:
            cfg = load_config()
            assert cfg.work_dir == ".partial_env"
            assert cfg.lite_base_url == "https://api.lite.example.com/v1"
        finally:
            os.environ.pop("GRAVIX_WORK_DIR", None)

    def test_missing_all_keys(self, tmp_workdir: Path) -> None:
        with pytest.raises(SystemExit, match="1"):
            load_config()

    def test_missing_one_key(self, tmp_workdir: Path) -> None:
        import yaml

        # Write config with only 4 of 5 keys (full_sk missing)
        partial = {
            "work_dir": ".gravix",
            "lite_base_url": "https://a.com/v1",
            "lite_sk": "sk1",
            "full_base_url": "https://b.com/v1",
        }
        with open(tmp_workdir / "gravix_conf.yaml", "w") as f:
            yaml.dump(partial, f)
        os.environ.pop("GRAVIX_FULL_SK", None)
        with pytest.raises(SystemExit, match="1"):
            load_config()
