from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from gravix.app import Gravix
from gravix.config import GravixConfig
from gravix.storage import init_ladybug, init_raw_dir, init_sqlite, init_work_dir
from tests.conftest import write_config, write_env_file


def _make_config(**overrides) -> GravixConfig:
    defaults = dict(
        work_dir=".gravix",
        lite_base_url="https://api.lite.example.com/v1",
        lite_model="gpt-4o-mini",
        lite_key="sk-lite-test",
        full_base_url="https://api.full.example.com/v1",
        full_model="gpt-4o",
        full_key="sk-full-test",
    )
    defaults.update(overrides)
    return GravixConfig(**defaults)


def _init_workspace(tmp_path: Path) -> Path:
    work_dir = tmp_path / ".gravix"
    init_work_dir(str(work_dir))
    init_ladybug(work_dir)
    init_sqlite(work_dir)
    init_raw_dir(work_dir)
    return work_dir


class TestGravixInit:
    def test_init_creates_workspace(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.chdir(tmp_path)
        config = _make_config(work_dir=".gravix")
        gravix = Gravix(config)
        gravix.init()
        assert (tmp_path / ".gravix").is_dir()
        assert (tmp_path / ".gravix" / "graph.lbug").exists()
        assert (tmp_path / ".gravix" / "abstract.db").exists()
        assert (tmp_path / ".gravix" / "raw").is_dir()


class TestCheckWorkDir:
    def test_check_passes_when_initialized(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.chdir(tmp_path)
        _init_workspace(tmp_path)
        config = _make_config(work_dir=".gravix")
        gravix = Gravix(config)
        assert gravix.check_work_dir() is True

    def test_check_fails_when_no_work_dir(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.chdir(tmp_path)
        config = _make_config(work_dir=".gravix")
        gravix = Gravix(config)
        assert gravix.check_work_dir() is False

    def test_check_fails_when_missing_ladybug(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.chdir(tmp_path)
        work_dir = tmp_path / ".gravix"
        init_work_dir(str(work_dir))
        init_sqlite(work_dir)
        init_raw_dir(work_dir)
        # missing graph.lbug
        config = _make_config(work_dir=".gravix")
        gravix = Gravix(config)
        assert gravix.check_work_dir() is False

    def test_check_fails_when_missing_sqlite(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.chdir(tmp_path)
        work_dir = tmp_path / ".gravix"
        init_work_dir(str(work_dir))
        init_ladybug(work_dir)
        init_raw_dir(work_dir)
        # missing abstract.db
        config = _make_config(work_dir=".gravix")
        gravix = Gravix(config)
        assert gravix.check_work_dir() is False

    def test_check_fails_when_missing_raw(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.chdir(tmp_path)
        work_dir = tmp_path / ".gravix"
        init_work_dir(str(work_dir))
        init_ladybug(work_dir)
        init_sqlite(work_dir)
        # missing raw dir
        config = _make_config(work_dir=".gravix")
        gravix = Gravix(config)
        assert gravix.check_work_dir() is False


class TestSetTopic:
    def test_set_topic_with_text(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.chdir(tmp_path)
        _init_workspace(tmp_path)
        config = _make_config(work_dir=".gravix")
        gravix = Gravix(config)

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "SWIFT报文知识库摘要"

        with patch("gravix.app.OpenAI") as mock_openai_cls:
            mock_client = MagicMock()
            mock_client.chat.completions.create.return_value = mock_response
            mock_openai_cls.return_value = mock_client

            gravix.set_topic(text="一个SWIFT报文知识库，涉及MT报文和MX报文")

        topic_file = tmp_path / ".gravix" / "topic.md"
        assert topic_file.exists()
        assert topic_file.read_text(encoding="utf-8") == "SWIFT报文知识库摘要"

        mock_openai_cls.assert_called_once_with(
            base_url="https://api.full.example.com/v1",
            api_key="sk-full-test",
        )
        mock_client.chat.completions.create.assert_called_once()

    def test_set_topic_with_file(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.chdir(tmp_path)
        _init_workspace(tmp_path)
        config = _make_config(work_dir=".gravix")
        gravix = Gravix(config)

        input_file = tmp_path / "intro.txt"
        input_file.write_text("知识库内容描述", encoding="utf-8")

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "知识库摘要"

        with patch("gravix.app.OpenAI") as mock_openai_cls:
            mock_client = MagicMock()
            mock_client.chat.completions.create.return_value = mock_response
            mock_openai_cls.return_value = mock_client

            gravix.set_topic(file=str(input_file))

        topic_file = tmp_path / ".gravix" / "topic.md"
        assert topic_file.exists()
        assert topic_file.read_text(encoding="utf-8") == "知识库摘要"

    def test_set_topic_no_work_dir_fails(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.chdir(tmp_path)
        config = _make_config(work_dir=".gravix")
        gravix = Gravix(config)
        with pytest.raises(SystemExit, match="1"):
            gravix.set_topic(text="some text")

    def test_set_topic_no_input_fails(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.chdir(tmp_path)
        _init_workspace(tmp_path)
        config = _make_config(work_dir=".gravix")
        gravix = Gravix(config)
        with pytest.raises(SystemExit, match="1"):
            gravix.set_topic()

    def test_set_topic_file_not_found_fails(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.chdir(tmp_path)
        _init_workspace(tmp_path)
        config = _make_config(work_dir=".gravix")
        gravix = Gravix(config)
        with pytest.raises(SystemExit, match="1"):
            gravix.set_topic(file="/nonexistent/file.txt")

    def test_set_topic_uses_full_model(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.chdir(tmp_path)
        _init_workspace(tmp_path)
        config = _make_config(
            work_dir=".gravix",
            full_base_url="https://api.full.example.com/v1",
            full_model="gpt-4o",
            full_key="sk-full-test",
        )
        gravix = Gravix(config)

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "摘要"

        with patch("gravix.app.OpenAI") as mock_openai_cls:
            mock_client = MagicMock()
            mock_client.chat.completions.create.return_value = mock_response
            mock_openai_cls.return_value = mock_client

            gravix.set_topic(text="test input")

        mock_openai_cls.assert_called_once_with(
            base_url="https://api.full.example.com/v1",
            api_key="sk-full-test",
        )
        call_kwargs = mock_client.chat.completions.create.call_args
        assert call_kwargs.kwargs["model"] == "gpt-4o"
