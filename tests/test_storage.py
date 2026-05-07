import sqlite3
from pathlib import Path

import ladybug
import pytest

from gravix.storage import init_ladybug, init_raw_dir, init_sqlite, init_work_dir


class TestInitWorkDir:
    """Work directory creation with mkdir -p semantics."""

    def test_create_new_dir(self, tmp_path: Path) -> None:
        target = tmp_path / ".gravix"
        result = init_work_dir(str(target))
        assert result == target
        assert target.is_dir()

    def test_create_relative_path(self, tmp_workdir: Path) -> None:
        result = init_work_dir(".gravix")
        expected = tmp_workdir / ".gravix"
        assert result == expected
        assert expected.is_dir()

    def test_create_nested_dirs(self, tmp_path: Path) -> None:
        target = tmp_path / "a" / "b" / "c"
        result = init_work_dir(str(target))
        assert target.is_dir()

    def test_existing_dir_is_ok(self, tmp_path: Path) -> None:
        target = tmp_path / ".gravix"
        target.mkdir()
        result = init_work_dir(str(target))
        assert target.is_dir()

    def test_path_is_file_raises(self, tmp_path: Path) -> None:
        target = tmp_path / ".gravix"
        target.touch()
        with pytest.raises(SystemExit, match="1"):
            init_work_dir(str(target))

    def test_permission_denied_raises(self, tmp_path: Path) -> None:
        parent = tmp_path / "locked"
        parent.mkdir()
        parent.chmod(0o444)
        try:
            with pytest.raises(SystemExit, match="1"):
                init_work_dir(str(parent / "sub" / "dir"))
        finally:
            parent.chmod(0o755)


class TestInitLadybug:
    """Ladybug graph database initialization."""

    def test_creates_lbug_file(self, tmp_path: Path) -> None:
        init_ladybug(tmp_path)
        assert (tmp_path / "graph.lbug").exists()

    def test_creates_node_table(self, tmp_path: Path) -> None:
        init_ladybug(tmp_path)
        db = ladybug.Database(str(tmp_path / "graph.lbug"))
        conn = ladybug.Connection(db)
        result = conn.execute("CALL show_tables() RETURN *;")
        tables = set()
        while result.has_next():
            tables.add(result.get_next()[1])
        conn.close()
        db.close()
        assert "gravix_node" in tables

    def test_creates_rel_table(self, tmp_path: Path) -> None:
        init_ladybug(tmp_path)
        db = ladybug.Database(str(tmp_path / "graph.lbug"))
        conn = ladybug.Connection(db)
        result = conn.execute("CALL show_tables() RETURN *;")
        tables = set()
        while result.has_next():
            tables.add(result.get_next()[1])
        conn.close()
        db.close()
        assert "gravix_relation" in tables

    def test_idempotent(self, tmp_path: Path) -> None:
        init_ladybug(tmp_path)
        init_ladybug(tmp_path)
        db = ladybug.Database(str(tmp_path / "graph.lbug"))
        conn = ladybug.Connection(db)
        result = conn.execute("CALL show_tables() RETURN *;")
        tables = []
        while result.has_next():
            tables.append(result.get_next()[1])
        conn.close()
        db.close()
        assert tables.count("gravix_node") == 1
        assert tables.count("gravix_relation") == 1


class TestInitSqlite:
    """SQLite database initialization."""

    def test_creates_db_file(self, tmp_path: Path) -> None:
        init_sqlite(tmp_path)
        assert (tmp_path / "abstract.db").exists()

    def test_creates_gravix_document_table(self, tmp_path: Path) -> None:
        init_sqlite(tmp_path)
        conn = sqlite3.connect(str(tmp_path / "abstract.db"))
        cur = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='gravix_document';"
        )
        assert cur.fetchone() is not None
        conn.close()

    def test_creates_fts5_table(self, tmp_path: Path) -> None:
        init_sqlite(tmp_path)
        conn = sqlite3.connect(str(tmp_path / "abstract.db"))
        cur = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='gravix_document_fts';"
        )
        assert cur.fetchone() is not None
        conn.close()

    def test_document_table_schema(self, tmp_path: Path) -> None:
        init_sqlite(tmp_path)
        conn = sqlite3.connect(str(tmp_path / "abstract.db"))
        cur = conn.execute("PRAGMA table_info(gravix_document);")
        columns = {row[1] for row in cur.fetchall()}
        conn.close()
        assert columns == {"id", "path", "title", "abstract", "updated_at"}

    def test_idempotent(self, tmp_path: Path) -> None:
        init_sqlite(tmp_path)
        init_sqlite(tmp_path)
        conn = sqlite3.connect(str(tmp_path / "abstract.db"))
        cur = conn.execute(
            "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='gravix_document';"
        )
        assert cur.fetchone()[0] == 1
        conn.close()


class TestInitRawDir:
    """Raw document directory initialization."""

    def test_creates_raw_dir(self, tmp_path: Path) -> None:
        init_raw_dir(tmp_path)
        assert (tmp_path / "raw").is_dir()

    def test_existing_raw_dir_is_ok(self, tmp_path: Path) -> None:
        (tmp_path / "raw").mkdir()
        init_raw_dir(tmp_path)
        assert (tmp_path / "raw").is_dir()

    def test_raw_dir_is_file_raises(self, tmp_path: Path) -> None:
        (tmp_path / "raw").touch()
        with pytest.raises(SystemExit, match="1"):
            init_raw_dir(tmp_path)
