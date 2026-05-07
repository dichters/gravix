import os
from collections.abc import Generator
from pathlib import Path

import pytest

from gravix.config import load_config
from tests.conftest import clear_gravix_env, write_config, write_env_file


class TestLoadConfigFromYamlAndEnv:
    """work_dir from yaml, LLM credentials from .env."""

    def test_load_from_yaml_and_env_file(self, tmp_workdir: Path) -> None:
        """Load work_dir from yaml, credentials from .env."""
        write_config(tmp_workdir / "gravix_conf.yaml", work_dir=".my_gravix")
        write_env_file(tmp_workdir / ".env")
        cfg = load_config()
        assert cfg.work_dir == ".my_gravix"
        assert cfg.lite_base_url == "https://api.lite.example.com/v1"
        assert cfg.lite_key == "sk-lite-test"
        assert cfg.full_base_url == "https://api.full.example.com/v1"
        assert cfg.full_key == "sk-full-test"

    def test_default_work_dir(self, tmp_workdir: Path) -> None:
        """If work_dir not in yaml, use default .gravix."""
        # Create empty yaml
        (tmp_workdir / "gravix_conf.yaml").write_text("{}\n")
        write_env_file(tmp_workdir / ".env")
        cfg = load_config()
        assert cfg.work_dir == ".gravix"

    def test_no_yaml_file_uses_default_work_dir(self, tmp_workdir: Path) -> None:
        """No yaml file means default work_dir, credentials still from .env."""
        write_env_file(tmp_workdir / ".env")
        cfg = load_config()
        assert cfg.work_dir == ".gravix"


class TestLoadConfigFromSystemEnv:
    """LLM credentials from system environment variables."""

    ENV_MAP = {
        "GRAVIX_LITE_BASE_URL": "https://env.lite.example.com/v1",
        "GRAVIX_LITE_KEY": "sk-env-lite",
        "GRAVIX_FULL_BASE_URL": "https://env.full.example.com/v1",
        "GRAVIX_FULL_KEY": "sk-env-full",
    }

    @pytest.fixture(autouse=True)
    def _set_env(self, tmp_workdir: Path) -> Generator[None, None, None]:
        """Set env vars after tmp_workdir has been set up."""
        # tmp_workdir clears env vars first, then we set them
        for k, v in self.ENV_MAP.items():
            os.environ[k] = v
        yield
        clear_gravix_env()

    def test_load_all_from_system_env(self) -> None:
        """All credentials from system environment variables."""
        write_config(Path.cwd() / "gravix_conf.yaml")
        cfg = load_config()
        assert cfg.work_dir == ".gravix"
        assert cfg.lite_base_url == "https://env.lite.example.com/v1"
        assert cfg.lite_key == "sk-env-lite"
        assert cfg.full_base_url == "https://env.full.example.com/v1"
        assert cfg.full_key == "sk-env-full"


class TestEnvOverridesDotenv:
    """System environment variables override .env file."""

    ENV_MAP = {
        "GRAVIX_LITE_BASE_URL": "https://override.lite.example.com/v1",
        "GRAVIX_LITE_KEY": "sk-override-lite",
    }

    @pytest.fixture(autouse=True)
    def _set_env(self, tmp_workdir: Path) -> Generator[None, None, None]:
        """Set env vars after tmp_workdir has been set up."""
        for k, v in self.ENV_MAP.items():
            os.environ[k] = v
        yield
        clear_gravix_env()

    def test_system_env_overrides_dotenv(self) -> None:
        """System env takes priority over .env file."""
        write_config(Path.cwd() / "gravix_conf.yaml")
        # .env has different values for lite_*, but system env should override
        write_env_file(
            Path.cwd() / ".env",
            lite_base_url="https://dotenv.lite.example.com/v1",
            lite_key="sk-dotenv-lite",
        )
        cfg = load_config()
        assert cfg.lite_base_url == "https://override.lite.example.com/v1"
        assert cfg.lite_key == "sk-override-lite"
        # Other values from .env
        assert cfg.full_base_url == "https://api.full.example.com/v1"
        assert cfg.full_key == "sk-full-test"


class TestMissingCredentials:
    """Error handling when LLM credentials are missing."""

    def test_missing_all_credentials(self, tmp_workdir: Path) -> None:
        """No credentials anywhere should fail."""
        clear_gravix_env()
        write_config(tmp_workdir / "gravix_conf.yaml")
        with pytest.raises(SystemExit, match="1"):
            load_config()

    def test_missing_one_credential(self, tmp_workdir: Path) -> None:
        """Missing one credential should fail."""
        clear_gravix_env()
        write_config(tmp_workdir / "gravix_conf.yaml")
        # Write .env with missing GRAVIX_LITE_KEY
        lines = [
            "GRAVIX_LITE_BASE_URL=https://a.com/v1",
            # Missing GRAVIX_LITE_KEY
            "GRAVIX_FULL_BASE_URL=https://b.com/v1",
            "GRAVIX_FULL_KEY=sk-full",
        ]
        (tmp_workdir / ".env").write_text("\n".join(lines) + "\n")
        with pytest.raises(SystemExit, match="1"):
            load_config()

    def test_empty_credential_value(self, tmp_workdir: Path) -> None:
        """Empty credential value should fail."""
        clear_gravix_env()
        write_config(tmp_workdir / "gravix_conf.yaml")
        write_env_file(
            tmp_workdir / ".env",
            lite_key="",  # Empty
        )
        with pytest.raises(SystemExit, match="1"):
            load_config()


class TestCustomConfigFile:
    """Using a custom config file path."""

    def test_custom_yaml_file(self, tmp_workdir: Path) -> None:
        """Load from custom yaml file path."""
        custom = tmp_workdir / "my_conf.yaml"
        write_config(custom, work_dir=".custom_work")
        write_env_file(tmp_workdir / ".env")
        cfg = load_config(config_file=str(custom))
        assert cfg.work_dir == ".custom_work"
