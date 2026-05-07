import sqlite3
from pathlib import Path

import ladybug
from loguru import logger as log


def _mkdir_p(path: Path) -> None:
    try:
        path.mkdir(parents=True, exist_ok=True)
    except FileExistsError:
        log.error("'{}' exists and is a file, cannot create directory", path)
        raise SystemExit(1)
    except PermissionError:
        log.error("Permission denied creating directory: {}", path)
        raise SystemExit(1)


def init_work_dir(work_dir: str) -> Path:
    p = Path(work_dir)
    if not p.is_absolute():
        p = Path.cwd() / p
    _mkdir_p(p)
    log.info("Work directory ready: {}", p)
    return p


def init_ladybug(work_dir: Path) -> None:
    db_path = work_dir / "graph.lbug"
    db = ladybug.Database(str(db_path))
    conn = ladybug.Connection(db)

    existing = set()
    try:
        result = conn.execute("CALL show_tables() RETURN *;")
        while result.has_next():
            row = result.get_next()
            existing.add(row[1])
    except Exception:
        pass

    if "gravix_node" not in existing:
        conn.execute(
            "CREATE NODE TABLE gravix_node ("
            "id STRING, ref STRING, kind STRING, label STRING, "
            "PRIMARY KEY (id));"
        )
        log.info("Created ladybug node table: gravix_node")
    else:
        log.info("Ladybug node table already exists: gravix_node")

    if "gravix_relation" not in existing:
        conn.execute(
            f"CREATE REL TABLE gravix_relation ("
            f"FROM gravix_node TO gravix_node, "
            f"relation_weight STRING, `desc` STRING);"
        )
        log.info("Created ladybug rel table: gravix_relation")
    else:
        log.info("Ladybug rel table already exists: gravix_relation")

    conn.close()
    db.close()
    log.info("Ladybug database initialized: {}", db_path)


def init_sqlite(work_dir: Path) -> None:
    db_path = work_dir / "abstract.db"
    conn = sqlite3.connect(str(db_path))

    conn.execute(
        f"CREATE TABLE IF NOT EXISTS gravix_document ("
        f"id INTEGER PRIMARY KEY AUTOINCREMENT, "
        f"path TEXT NOT NULL UNIQUE, "
        f"title TEXT, "
        f"abstract TEXT, "
        f"updated_at DATETIME DEFAULT CURRENT_TIMESTAMP);"
    )

    conn.execute(
        f"CREATE VIRTUAL TABLE IF NOT EXISTS gravix_document_fts USING fts5("
        f"title, abstract, content='gravix_document', content_rowid='id');"
    )

    conn.commit()
    conn.close()
    log.info("SQLite database initialized: {}", db_path)


def init_raw_dir(work_dir: Path) -> None:
    raw_path = work_dir / "raw"
    _mkdir_p(raw_path)
    log.info("Raw directory ready: {}", raw_path)
