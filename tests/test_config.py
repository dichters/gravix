import json
import os
from collections.abc import Generator
from pathlib import Path

import pytest

from gravix.config import DEFAULT_CONFIG_FILE, load_config
from tests.conftest import clear_gravix_env, write_config, write_config_missing_llm, write_env_file


class TestLoadConfigFromJsonAndEnv:
    """work_dir and llm settings from json, API keys from .env."""

    def test_load_from_json_and_env_file(self, tmp_workdir: Path) -> None:
        """Load work_dir and llm from json, keys from .env."""
        write_config(tmp_workdir / DEFAULT_CONFIG_FILE, work_dir=".my_gravix")
        write_env_file(tmp_workdir / ".env")
        cfg = load_config()
        assert cfg.work_dir == ".my_gravix"
        assert cfg.lite_base_url == "https://api.lite.example.com/v1"
        assert cfg.lite_model == "gpt-4o-mini"
        assert cfg.lite_key == "sk-lite-test"
        assert cfg.full_base_url == "https://api.full.example.com/v1"
        assert cfg.full_model == "gpt-4o"
        assert cfg.full_key == "sk-full-test"

    def test_default_work_dir(self, tmp_workdir: Path) -> None:
        """If work_dir not in json, use default .gravix."""
        data = {
            "llm": {
                "lite": {"base_url": "https://a.com/v1", "model": "m1"},
                "full": {"base_url": "https://b.com/v1", "model": "m2"},
            }
        }
        (tmp_workdir / DEFAULT_CONFIG_FILE).write_text(json.dumps(data, indent=2))
        write_env_file(tmp_workdir / ".env")
        cfg = load_config()
        assert cfg.work_dir == ".gravix"

    def test_no_json_file_fails_missing_llm(self, tmp_workdir: Path) -> None:
        """No json file means missing required llm config, should fail."""
        write_env_file(tmp_workdir / ".env")
        with pytest.raises(SystemExit, match="1"):
            load_config()


class TestLoadConfigFromSystemEnv:
    """LLM API keys from system environment variables."""

    ENV_MAP = {
        "GRAVIX_LITE_KEY": "sk-env-lite",
        "GRAVIX_FULL_KEY": "sk-env-full",
    }

    @pytest.fixture(autouse=True)
    def _set_env(self, tmp_workdir: Path) -> Generator[None, None, None]:
        """Set env vars after tmp_workdir has been set up."""
        for k, v in self.ENV_MAP.items():
            os.environ[k] = v
        yield
        clear_gravix_env()

    def test_load_keys_from_system_env(self) -> None:
        """API keys from system environment variables, llm from json."""
        write_config(Path.cwd() / DEFAULT_CONFIG_FILE)
        cfg = load_config()
        assert cfg.work_dir == ".gravix"
        assert cfg.lite_base_url == "https://api.lite.example.com/v1"
        assert cfg.lite_model == "gpt-4o-mini"
        assert cfg.lite_key == "sk-env-lite"
        assert cfg.full_base_url == "https://api.full.example.com/v1"
        assert cfg.full_model == "gpt-4o"
        assert cfg.full_key == "sk-env-full"


class TestEnvOverridesDotenv:
    """System environment variables override .env file for API keys."""

    ENV_MAP = {
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
        """System env takes priority over .env file for keys."""
        write_config(Path.cwd() / DEFAULT_CONFIG_FILE)
        # .env has different value for lite_key, but system env should override
        write_env_file(
            Path.cwd() / ".env",
            lite_key="sk-dotenv-lite",
        )
        cfg = load_config()
        assert cfg.lite_key == "sk-override-lite"
        # Other values from .env
        assert cfg.full_key == "sk-full-test"


class TestMissingLlmInJson:
    """Error handling when required llm fields are missing from json."""

    def test_missing_llm_section_entirely(self, tmp_workdir: Path) -> None:
        """No llm section in json should fail."""
        clear_gravix_env()
        write_config_missing_llm(tmp_workdir / DEFAULT_CONFIG_FILE)
        write_env_file(tmp_workdir / ".env")
        with pytest.raises(SystemExit, match="1"):
            load_config()

    def test_missing_lite_section(self, tmp_workdir: Path) -> None:
        """Missing lite section in llm should fail."""
        clear_gravix_env()
        write_config_missing_llm(
            tmp_workdir / DEFAULT_CONFIG_FILE,
            llm={"full": {"base_url": "https://b.com/v1", "model": "m2"}},
        )
        write_env_file(tmp_workdir / ".env")
        with pytest.raises(SystemExit, match="1"):
            load_config()

    def test_missing_full_section(self, tmp_workdir: Path) -> None:
        """Missing full section in llm should fail."""
        clear_gravix_env()
        write_config_missing_llm(
            tmp_workdir / DEFAULT_CONFIG_FILE,
            llm={"lite": {"base_url": "https://a.com/v1", "model": "m1"}},
        )
        write_env_file(tmp_workdir / ".env")
        with pytest.raises(SystemExit, match="1"):
            load_config()

    def test_missing_lite_base_url(self, tmp_workdir: Path) -> None:
        """Missing lite.base_url should fail."""
        clear_gravix_env()
        write_config_missing_llm(
            tmp_workdir / DEFAULT_CONFIG_FILE,
            llm={
                "lite": {"model": "m1"},
                "full": {"base_url": "https://b.com/v1", "model": "m2"},
            },
        )
        write_env_file(tmp_workdir / ".env")
        with pytest.raises(SystemExit, match="1"):
            load_config()

    def test_missing_lite_model(self, tmp_workdir: Path) -> None:
        """Missing lite.model should fail."""
        clear_gravix_env()
        write_config_missing_llm(
            tmp_workdir / DEFAULT_CONFIG_FILE,
            llm={
                "lite": {"base_url": "https://a.com/v1"},
                "full": {"base_url": "https://b.com/v1", "model": "m2"},
            },
        )
        write_env_file(tmp_workdir / ".env")
        with pytest.raises(SystemExit, match="1"):
            load_config()

    def test_missing_full_base_url(self, tmp_workdir: Path) -> None:
        """Missing full.base_url should fail."""
        clear_gravix_env()
        write_config_missing_llm(
            tmp_workdir / DEFAULT_CONFIG_FILE,
            llm={
                "lite": {"base_url": "https://a.com/v1", "model": "m1"},
                "full": {"model": "m2"},
            },
        )
        write_env_file(tmp_workdir / ".env")
        with pytest.raises(SystemExit, match="1"):
            load_config()

    def test_missing_full_model(self, tmp_workdir: Path) -> None:
        """Missing full.model should fail."""
        clear_gravix_env()
        write_config_missing_llm(
            tmp_workdir / DEFAULT_CONFIG_FILE,
            llm={
                "lite": {"base_url": "https://a.com/v1", "model": "m1"},
                "full": {"base_url": "https://b.com/v1"},
            },
        )
        write_env_file(tmp_workdir / ".env")
        with pytest.raises(SystemExit, match="1"):
            load_config()

    def test_empty_llm_field_value(self, tmp_workdir: Path) -> None:
        """Empty string for a required llm field should fail."""
        clear_gravix_env()
        write_config(
            tmp_workdir / DEFAULT_CONFIG_FILE,
            lite_base_url="",
        )
        write_env_file(tmp_workdir / ".env")
        with pytest.raises(SystemExit, match="1"):
            load_config()

    def test_whitespace_only_llm_field_value(self, tmp_workdir: Path) -> None:
        """Whitespace-only value for a required llm field should fail."""
        clear_gravix_env()
        write_config(
            tmp_workdir / DEFAULT_CONFIG_FILE,
            lite_model="   ",
        )
        write_env_file(tmp_workdir / ".env")
        with pytest.raises(SystemExit, match="1"):
            load_config()

    def test_invalid_json_file(self, tmp_workdir: Path) -> None:
        """Invalid json content should fail."""
        clear_gravix_env()
        (tmp_workdir / DEFAULT_CONFIG_FILE).write_text("{invalid json!!!")
        write_env_file(tmp_workdir / ".env")
        with pytest.raises(SystemExit, match="1"):
            load_config()

    def test_json_file_with_non_dict_root(self, tmp_workdir: Path) -> None:
        """Json file with array root (not dict) should fail."""
        clear_gravix_env()
        (tmp_workdir / DEFAULT_CONFIG_FILE).write_text("[1, 2, 3]")
        write_env_file(tmp_workdir / ".env")
        with pytest.raises(SystemExit, match="1"):
            load_config()

    def test_json_file_with_null_llm(self, tmp_workdir: Path) -> None:
        """Json with llm: null should fail."""
        clear_gravix_env()
        (tmp_workdir / DEFAULT_CONFIG_FILE).write_text('{"llm": null}')
        write_env_file(tmp_workdir / ".env")
        with pytest.raises(SystemExit, match="1"):
            load_config()


class TestMissingCredentials:
    """Error handling when API keys are missing."""

    def test_missing_all_keys(self, tmp_workdir: Path) -> None:
        """No API keys anywhere should fail."""
        clear_gravix_env()
        write_config(tmp_workdir / DEFAULT_CONFIG_FILE)
        with pytest.raises(SystemExit, match="1"):
            load_config()

    def test_missing_one_key(self, tmp_workdir: Path) -> None:
        """Missing one API key should fail."""
        clear_gravix_env()
        write_config(tmp_workdir / DEFAULT_CONFIG_FILE)
        lines = [
            # Missing GRAVIX_LITE_KEY
            "GRAVIX_FULL_KEY=sk-full",
        ]
        (tmp_workdir / ".env").write_text("\n".join(lines) + "\n")
        with pytest.raises(SystemExit, match="1"):
            load_config()

    def test_empty_key_value(self, tmp_workdir: Path) -> None:
        """Empty key value should fail."""
        clear_gravix_env()
        write_config(tmp_workdir / DEFAULT_CONFIG_FILE)
        write_env_file(
            tmp_workdir / ".env",
            lite_key="",
        )
        with pytest.raises(SystemExit, match="1"):
            load_config()


class TestCustomConfigFile:
    """Using a custom config file path."""

    def test_custom_json_file(self, tmp_workdir: Path) -> None:
        """Load from custom json file path."""
        custom = tmp_workdir / "my_conf.json"
        write_config(custom, work_dir=".custom_work")
        write_env_file(tmp_workdir / ".env")
        cfg = load_config(config_file=str(custom))
        assert cfg.work_dir == ".custom_work"
