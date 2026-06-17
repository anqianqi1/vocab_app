from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from vocab_pipeline.db import build_word_database


def test_build_word_database_populates_word_entries(tmp_path: Path) -> None:
    words_path = tmp_path / "words.json"
    words_path.write_text(
        json.dumps(
            [
                {
                    "word": "gradually",
                    "grade": 4,
                    "lesson_number": 1,
                    "lesson_title": "Good Sense Across the Grades",
                    "group": "key",
                    "root": "GRAD",
                    "root_meaning": "step",
                    "root_origin": "Latin",
                    "part_of_speech": "adv.",
                    "definition": "little by little",
                    "example": "The snow melted gradually.",
                    "related_words": {"same_root": ["graduate"], "same_lesson": ["graduate"]},
                    "exercises": [{"title": "Exercise A", "lines": ["Use the root clue."]}],
                }
            ],
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    db_path = tmp_path / "vocabulary.sqlite"
    summary = build_word_database(words_path, db_path=db_path, category="grade-4")

    assert summary["word_count"] == 1
    assert db_path.exists()

    with sqlite3.connect(db_path) as connection:
        row = connection.execute(
            'SELECT word, grade, lesson_number, "group", root, definition FROM word_entries WHERE word = ?',
            ("gradually",),
        ).fetchone()

    assert row is not None
    assert row[0] == "gradually"
    assert row[1] == 4
    assert row[2] == 1
    assert row[3] == "key"
    assert row[4] == "GRAD"
    assert row[5] == "little by little"
