"""Tests for gravix CLI commands."""

from pathlib import Path

import pytest

from gravix.cli import main
from tests.conftest import write_config, write_env_file


class TestInitCommand:
    """Tests for `gravix init` command."""

    def test_init_default(self, tmp_workdir: Path, capsys) -> None:
        """Init with default work_dir from config."""
        from io import StringIO
        import sys

        write_config(tmp_workdir / "gravix_conf.json")
        write_env_file(tmp_workdir / ".env")

        # Simulate command line args
        sys.argv = ["gravix", "init"]
        try:
            main()
        except SystemExit:
            pass

        assert (tmp_workdir / ".gravix").exists()

    def test_init_with_custom_work_dir_in_config(self, tmp_workdir: Path) -> None:
        """Init with work_dir from config."""
        import sys

        write_config(tmp_workdir / "gravix_conf.json", work_dir=".config_dir")
        write_env_file(tmp_workdir / ".env")

        sys.argv = ["gravix", "init"]
        try:
            main()
        except SystemExit:
            pass

        assert (tmp_workdir / ".config_dir").exists()

    def test_init_with_conf_option(self, tmp_workdir: Path) -> None:
        """Init with -conf option to specify config file."""
        import sys

        write_config(tmp_workdir / "my_conf.json", work_dir=".custom_dir")
        write_env_file(tmp_workdir / ".env")

        sys.argv = ["gravix", "init", "-conf", "my_conf.json"]
        try:
            main()
        except SystemExit:
            pass

        assert (tmp_workdir / ".custom_dir").exists()

    def test_init_missing_credentials(self, tmp_workdir: Path) -> None:
        """Init without credentials should fail."""
        import sys

        write_config(tmp_workdir / "gravix_conf.json")
        # No .env file

        sys.argv = ["gravix", "init"]
        with pytest.raises(SystemExit, match="1"):
            main()


class TestTopicCommand:
    """Tests for `gravix topic` command."""

    def test_topic_with_text(self, tmp_workdir: Path) -> None:
        """Set topic with inline text."""
        import sys
        from unittest.mock import MagicMock, patch

        from gravix.storage import init_ladybug, init_raw_dir, init_sqlite, init_work_dir

        write_config(tmp_workdir / "gravix_conf.json")
        write_env_file(tmp_workdir / ".env")
        init_work_dir(str(tmp_workdir / ".gravix"))
        init_ladybug(tmp_workdir / ".gravix")
        init_sqlite(tmp_workdir / ".gravix")
        init_raw_dir(tmp_workdir / ".gravix")

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "摘要结果"

        with patch("gravix.app.OpenAI") as mock_openai_cls:
            mock_client = MagicMock()
            mock_client.chat.completions.create.return_value = mock_response
            mock_openai_cls.return_value = mock_client

            sys.argv = ["gravix", "topic", "知识库描述"]
            main()

        assert (tmp_workdir / ".gravix" / "topic.md").exists()
        assert (tmp_workdir / ".gravix" / "topic.md").read_text(encoding="utf-8") == "摘要结果"

    def test_topic_with_file(self, tmp_workdir: Path) -> None:
        """Set topic with -file option."""
        import sys
        from unittest.mock import MagicMock, patch

        from gravix.storage import init_ladybug, init_raw_dir, init_sqlite, init_work_dir

        write_config(tmp_workdir / "gravix_conf.json")
        write_env_file(tmp_workdir / ".env")
        init_work_dir(str(tmp_workdir / ".gravix"))
        init_ladybug(tmp_workdir / ".gravix")
        init_sqlite(tmp_workdir / ".gravix")
        init_raw_dir(tmp_workdir / ".gravix")

        (tmp_workdir / "intro.txt").write_text("文件内容描述", encoding="utf-8")

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "文件摘要"

        with patch("gravix.app.OpenAI") as mock_openai_cls:
            mock_client = MagicMock()
            mock_client.chat.completions.create.return_value = mock_response
            mock_openai_cls.return_value = mock_client

            sys.argv = ["gravix", "topic", "-file", str(tmp_workdir / "intro.txt")]
            main()

        assert (tmp_workdir / ".gravix" / "topic.md").exists()

    def test_topic_without_init_fails(self, tmp_workdir: Path) -> None:
        """Set topic without prior init should fail."""
        import sys

        write_config(tmp_workdir / "gravix_conf.json")
        write_env_file(tmp_workdir / ".env")

        sys.argv = ["gravix", "topic", "some text"]
        with pytest.raises(SystemExit, match="1"):
            main()


class TestCliHelp:
    """Tests for CLI help."""

    def test_cli_help(self, tmp_workdir: Path) -> None:
        """CLI --help should show help message."""
        import sys

        sys.argv = ["gravix", "--help"]
        try:
            main()
        except SystemExit:
            pass

    def test_cli_no_command(self, tmp_workdir: Path) -> None:
        """CLI with no command should show help."""
        import sys

        sys.argv = ["gravix"]
        try:
            main()
        except SystemExit:
            pass
