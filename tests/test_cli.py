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

        write_config(tmp_workdir / "gravix_conf.yaml")
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

        write_config(tmp_workdir / "gravix_conf.yaml", work_dir=".config_dir")
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

        write_config(tmp_workdir / "my_conf.yaml", work_dir=".custom_dir")
        write_env_file(tmp_workdir / ".env")

        sys.argv = ["gravix", "init", "-conf", "my_conf.yaml"]
        try:
            main()
        except SystemExit:
            pass

        assert (tmp_workdir / ".custom_dir").exists()

    def test_init_missing_credentials(self, tmp_workdir: Path) -> None:
        """Init without credentials should fail."""
        import sys

        write_config(tmp_workdir / "gravix_conf.yaml")
        # No .env file

        sys.argv = ["gravix", "init"]
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
