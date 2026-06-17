from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from .ids import normalize_category
from .json_io import ensure_parent, read_json, read_jsonl
from .paths import PipelinePaths


WORD_ENTRY_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS word_entries (
    id TEXT PRIMARY KEY,
    word TEXT NOT NULL,
    grade INTEGER NOT NULL,
    lesson_number INTEGER NOT NULL,
    lesson_title TEXT NOT NULL DEFAULT '',
    "group" TEXT NOT NULL DEFAULT 'key',
    root TEXT NOT NULL DEFAULT '',
    root_meaning TEXT NOT NULL DEFAULT '',
    root_origin TEXT NOT NULL DEFAULT '',
    part_of_speech TEXT NOT NULL DEFAULT '',
    definition TEXT NOT NULL DEFAULT '',
    example TEXT NOT NULL DEFAULT '',
    category TEXT NOT NULL DEFAULT 'uncategorized',
    related_words_json TEXT NOT NULL DEFAULT '{}',
    exercises_json TEXT NOT NULL DEFAULT '[]',
    image_path TEXT NOT NULL DEFAULT '',
    image_source TEXT NOT NULL DEFAULT '',
    source_path TEXT NOT NULL DEFAULT ''
);

CREATE INDEX IF NOT EXISTS idx_word_entries_grade ON word_entries(grade);
CREATE INDEX IF NOT EXISTS idx_word_entries_category ON word_entries(category);
CREATE INDEX IF NOT EXISTS idx_word_entries_word ON word_entries(word);
"""


def default_db_output(content_root: Path = Path("content")) -> Path:
    paths = PipelinePaths(content_root=content_root)
    return paths.db_path()


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
            related_terms_json TEXT NOT NULL DEFAULT '[]',
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
    ensure_column(connection, "entries", "related_terms_json", "related_terms_json TEXT NOT NULL DEFAULT '[]'")
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
            raw_entry_text, parser_profile, parser_version, review_status, warnings_json,
            related_terms_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
            warnings_json = excluded.warnings_json,
            related_terms_json = excluded.related_terms_json
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
            json.dumps(entry.get("related_terms") or [], ensure_ascii=False),
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


def build_word_database(words_path: Path, db_path: Path | None = None, category: str | None = None) -> dict[str, Any]:
    with words_path.open("r", encoding="utf-8") as file_handle:
        words_value = json.load(file_handle)
    if not isinstance(words_value, list):
        raise ValueError(f"Expected a JSON array in {words_path}")
    words = words_value
    selected_db_path = db_path or default_db_output()

    with connect_database(selected_db_path) as connection:
        connection.executescript(WORD_ENTRY_SCHEMA_SQL)
        ensure_column(connection, "word_entries", "image_path", "image_path TEXT NOT NULL DEFAULT ''")
        ensure_column(connection, "word_entries", "image_source", "image_source TEXT NOT NULL DEFAULT ''")
        grades_in_bundle = sorted({int(word_entry.get("grade") or 0) for word_entry in words})
        if grades_in_bundle:
            placeholders = ",".join("?" for _ in grades_in_bundle)
            connection.execute(
                f"DELETE FROM word_entries WHERE grade IN ({placeholders})",
                grades_in_bundle,
            )
        for word_entry in words:
            connection.execute(
                """
                INSERT INTO word_entries (
                    id, word, grade, lesson_number, lesson_title, "group", root, root_meaning,
                    root_origin, part_of_speech, definition, example, category, related_words_json,
                    exercises_json, image_path, image_source, source_path
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    word = excluded.word,
                    grade = excluded.grade,
                    lesson_number = excluded.lesson_number,
                    lesson_title = excluded.lesson_title,
                    "group" = excluded."group",
                    root = excluded.root,
                    root_meaning = excluded.root_meaning,
                    root_origin = excluded.root_origin,
                    part_of_speech = excluded.part_of_speech,
                    definition = excluded.definition,
                    example = excluded.example,
                    category = excluded.category,
                    related_words_json = excluded.related_words_json,
                    exercises_json = excluded.exercises_json,
                    image_path = excluded.image_path,
                    image_source = excluded.image_source,
                    source_path = excluded.source_path
                """,
                (
                    f"{word_entry.get('word') or ''}:{word_entry.get('grade') or 0}:{word_entry.get('lesson_number') or 0}",
                    word_entry.get("word") or "",
                    word_entry.get("grade") or 0,
                    word_entry.get("lesson_number") or 0,
                    word_entry.get("lesson_title") or "",
                    word_entry.get("group") or "key",
                    word_entry.get("root") or "",
                    word_entry.get("root_meaning") or "",
                    word_entry.get("root_origin") or "",
                    word_entry.get("part_of_speech") or "",
                    word_entry.get("definition") or "",
                    word_entry.get("example") or "",
                    normalize_category(category) if category else word_entry.get("category") or "uncategorized",
                    json.dumps(word_entry.get("related_words") or {}, ensure_ascii=False),
                    json.dumps(word_entry.get("exercises") or [], ensure_ascii=False),
                    word_entry.get("image") or word_entry.get("image_path") or "",
                    word_entry.get("image_source") or "",
                    str(words_path),
                ),
            )
        connection.commit()

    return {
        "db_path": str(selected_db_path),
        "word_count": len(words),
        "category": normalize_category(category) if category else None,
    }


def list_words(grade: int, db_path: Path | None = None) -> list[dict[str, Any]]:
    """Return all word entries for a grade, decoding JSON columns into nested data."""
    selected_db_path = db_path or default_db_output()
    with connect_database(selected_db_path) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(
            """
            SELECT word, grade, lesson_number, lesson_title, "group", root, root_meaning,
                   root_origin, part_of_speech, definition, example, category,
                   related_words_json, exercises_json, image_path, image_source
            FROM word_entries
            WHERE grade = ?
            ORDER BY lesson_number, "group", word
            """,
            (grade,),
        ).fetchall()

    words: list[dict[str, Any]] = []
    for row in rows:
        record = dict(row)
        record["related_words"] = json.loads(record.pop("related_words_json") or "{}")
        record["exercises"] = json.loads(record.pop("exercises_json") or "[]")
        record["image"] = record.pop("image_path", "")
        words.append(record)
    return words
