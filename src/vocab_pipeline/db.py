from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from .json_io import ensure_parent, read_json, read_jsonl


def default_db_output(data_root: Path = Path("data")) -> Path:
    return data_root / "db" / "vocabulary.sqlite"


def connect_database(db_path: Path) -> sqlite3.Connection:
    ensure_parent(db_path)
    connection = sqlite3.connect(db_path)
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def ensure_column(connection: sqlite3.Connection, table_name: str, column_name: str, column_sql: str) -> None:
    existing_columns = {
        row[1] for row in connection.execute(f"PRAGMA table_info({table_name})").fetchall()
    }
    if column_name not in existing_columns:
        connection.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_sql}")


def initialize_schema(connection: sqlite3.Connection) -> bool:
    connection.executescript(
        """
        CREATE TABLE IF NOT EXISTS sources (
            source_id TEXT PRIMARY KEY,
            category TEXT NOT NULL DEFAULT 'uncategorized',
            source_title TEXT,
            file_name TEXT NOT NULL,
            file_path TEXT,
            file_sha256 TEXT,
            page_count INTEGER NOT NULL DEFAULT 0,
            extracted_at TEXT,
            extraction_engine TEXT,
            warnings_json TEXT NOT NULL DEFAULT '[]'
        );

        CREATE TABLE IF NOT EXISTS entries (
            id TEXT PRIMARY KEY,
            term TEXT NOT NULL,
            normalized_term TEXT NOT NULL,
            definition TEXT NOT NULL DEFAULT '',
            part_of_speech TEXT,
            root_or_origin TEXT,
            example TEXT,
            section TEXT,
            category TEXT NOT NULL DEFAULT 'uncategorized',
            source_id TEXT NOT NULL,
            source_page INTEGER NOT NULL,
            source_order INTEGER NOT NULL,
            raw_entry_text TEXT NOT NULL DEFAULT '',
            parser_profile TEXT NOT NULL DEFAULT 'generic',
            parser_version TEXT NOT NULL,
            review_status TEXT NOT NULL,
            warnings_json TEXT NOT NULL DEFAULT '[]',
            FOREIGN KEY (source_id) REFERENCES sources(source_id) ON DELETE CASCADE
        );

        CREATE INDEX IF NOT EXISTS idx_entries_normalized_term ON entries(normalized_term);
        CREATE INDEX IF NOT EXISTS idx_entries_source ON entries(source_id, source_page, source_order);
        """
    )
    ensure_column(connection, "sources", "category", "category TEXT NOT NULL DEFAULT 'uncategorized'")
    ensure_column(connection, "sources", "source_title", "source_title TEXT")
    ensure_column(connection, "entries", "category", "category TEXT NOT NULL DEFAULT 'uncategorized'")
    ensure_column(connection, "entries", "parser_profile", "parser_profile TEXT NOT NULL DEFAULT 'generic'")
    connection.execute("CREATE INDEX IF NOT EXISTS idx_entries_category ON entries(category)")

    fts_enabled = True
    try:
        connection.execute(
            """
            CREATE VIRTUAL TABLE IF NOT EXISTS entries_fts USING fts5(
                term,
                definition,
                raw_entry_text,
                content='entries',
                content_rowid='rowid'
            )
            """
        )
    except sqlite3.OperationalError:
        fts_enabled = False
    return fts_enabled


def upsert_source(connection: sqlite3.Connection, source: dict[str, Any]) -> None:
    connection.execute(
        """
        INSERT INTO sources (
            source_id, category, source_title, file_name, file_path, file_sha256,
            page_count, extracted_at, extraction_engine, warnings_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(source_id) DO UPDATE SET
            category = excluded.category,
            source_title = excluded.source_title,
            file_name = excluded.file_name,
            file_path = excluded.file_path,
            file_sha256 = excluded.file_sha256,
            page_count = excluded.page_count,
            extracted_at = excluded.extracted_at,
            extraction_engine = excluded.extraction_engine,
            warnings_json = excluded.warnings_json
        """,
        (
            source.get("source_id"),
            source.get("category") or "uncategorized",
            source.get("source_title"),
            source.get("file_name"),
            source.get("file_path"),
            source.get("file_sha256"),
            source.get("page_count") or 0,
            source.get("extracted_at"),
            source.get("extraction_engine"),
            json.dumps(source.get("warnings") or [], ensure_ascii=False),
        ),
    )


def upsert_entry(connection: sqlite3.Connection, entry: dict[str, Any]) -> None:
    connection.execute(
        """
        INSERT INTO entries (
            id, term, normalized_term, definition, part_of_speech, root_or_origin,
            example, section, category, source_id, source_page, source_order,
            raw_entry_text, parser_profile, parser_version, review_status, warnings_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            term = excluded.term,
            normalized_term = excluded.normalized_term,
            definition = excluded.definition,
            part_of_speech = excluded.part_of_speech,
            root_or_origin = excluded.root_or_origin,
            example = excluded.example,
            section = excluded.section,
            category = excluded.category,
            source_id = excluded.source_id,
            source_page = excluded.source_page,
            source_order = excluded.source_order,
            raw_entry_text = excluded.raw_entry_text,
            parser_profile = excluded.parser_profile,
            parser_version = excluded.parser_version,
            review_status = excluded.review_status,
            warnings_json = excluded.warnings_json
        """,
        (
            entry.get("id"),
            entry.get("term") or "",
            entry.get("normalized_term") or "",
            entry.get("definition") or "",
            entry.get("part_of_speech"),
            entry.get("root_or_origin"),
            entry.get("example"),
            entry.get("section"),
            entry.get("category") or "uncategorized",
            entry.get("source_id"),
            entry.get("source_page") or 0,
            entry.get("source_order") or 0,
            entry.get("raw_entry_text") or "",
            entry.get("parser_profile") or "generic",
            entry.get("parser_version") or "unknown",
            entry.get("review_status") or "needs_review",
            json.dumps(entry.get("warnings") or [], ensure_ascii=False),
        ),
    )


def rebuild_fts(connection: sqlite3.Connection) -> None:
    connection.execute("DELETE FROM entries_fts")
    connection.execute(
        """
        INSERT INTO entries_fts(rowid, term, definition, raw_entry_text)
        SELECT rowid, term, definition, raw_entry_text FROM entries
        """
    )


def build_database(raw_path: Path, entries_path: Path, db_path: Path | None = None) -> dict[str, Any]:
    raw_payload = read_json(raw_path)
    entries = read_jsonl(entries_path)
    selected_db_path = db_path or default_db_output()

    with connect_database(selected_db_path) as connection:
        fts_enabled = initialize_schema(connection)
        upsert_source(connection, raw_payload.get("source", {}))
        for entry in entries:
            upsert_entry(connection, entry)
        if fts_enabled:
            rebuild_fts(connection)
        connection.commit()

    return {
        "db_path": str(selected_db_path),
        "source_id": raw_payload.get("source", {}).get("source_id"),
        "entry_count": len(entries),
        "fts_enabled": fts_enabled,
    }
