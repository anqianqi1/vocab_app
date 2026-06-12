from pathlib import Path

from vocab_pipeline.paths import PipelinePaths
from vocab_pipeline.structured_extraction import _build_word_entries


def test_lesson_and_word_bundle_paths_are_grade_prefixed() -> None:
    raw_path = Path("content/grade-4/raw/source.pages.json")
    paths = PipelinePaths()

    lessons_json, lessons_md = paths.lesson_bundle_paths_for_raw(raw_path)
    words_json = paths.words_output_path_for_raw(raw_path)

    assert lessons_json == Path("content/grade-4/lessons/grade-4_all_lessons_extraction.json")
    assert lessons_md == Path("content/grade-4/lessons/grade-4_all_lessons_extraction.md")
    assert words_json == Path("content/grade-4/lessons/grade-4_words.json")


def test_word_entries_match_roots_inside_words() -> None:
    lessons = [
        {
            "lesson_number": 1,
            "title": "Good Sense across the grades",
            "roots": [
                {"root": "GRAD", "origin": "Latin/Greek", "meaning": "step", "example_word": "gradus"},
                {"root": "SENS", "origin": "Latin/Greek", "meaning": "feeling", "example_word": "sensus"},
            ],
            "word_details": [
                {"word": "gradually", "group": "key", "senses": []},
                {"word": "downgrade", "group": "challenge", "senses": []},
                {"word": "sensitive", "group": "key", "senses": []},
                {"word": "extrasensory", "group": "challenge", "senses": []},
            ],
            "exercises": [],
        }
    ]

    entries = {entry["word"]: entry for entry in _build_word_entries(lessons, grade=4)}

    assert entries["downgrade"]["root"] == "GRAD"
    assert "gradually" in entries["downgrade"]["related_words"]["same_root"]
    assert entries["extrasensory"]["root"] == "SENS"
    assert "sensitive" in entries["extrasensory"]["related_words"]["same_root"]