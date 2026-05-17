from pathlib import Path

import pytest

from vocab_pipeline.extract import default_raw_output
from vocab_pipeline.parse import default_entries_output, parse_page_text, parse_raw_payload
from vocab_pipeline.validate import default_report_output


def test_parse_inline_entries() -> None:
    text = "abrogate - to abolish or repeal\nbenevolent: kind and generous"

    entries = parse_page_text(text)

    assert [entry["term"] for entry in entries] == ["abrogate", "benevolent"]
    assert entries[0]["definition"] == "to abolish or repeal"
    assert entries[0]["raw_entry_text"] == "abrogate - to abolish or repeal"
    assert entries[1]["definition"] == "kind and generous"
    assert entries[1]["raw_entry_text"] == "benevolent: kind and generous"


def test_parse_term_line_followed_by_definition() -> None:
    text = "Audible\nable to be heard\nVisible\nable to be seen"

    entries = parse_page_text(text)

    assert [entry["term"] for entry in entries] == ["Audible", "Visible"]
    assert entries[0]["definition"] == "able to be heard"
    assert entries[1]["definition"] == "able to be seen"


def test_parse_raw_payload_preserves_category_and_profile() -> None:
    raw_payload = {
        "source": {"source_id": "classical-roots-source", "category": "classical-roots"},
        "pages": [{"page": 7, "text": "Audible - able to be heard"}],
    }

    entries = parse_raw_payload(raw_payload, parser_profile="generic")

    assert len(entries) == 1
    assert entries[0]["category"] == "classical-roots"
    assert entries[0]["parser_profile"] == "generic"
    assert entries[0]["source_id"] == "classical-roots-source"
    assert entries[0]["source_page"] == 7


def test_parse_rejects_unknown_profile() -> None:
    with pytest.raises(ValueError, match="Unknown parser profile"):
        parse_page_text("Audible - able to be heard", parser_profile="unknown")


def test_raw_output_partitions_by_category() -> None:
    output_path = default_raw_output(Path("Vocabulary from Classical Roots.pdf"), category="Classical Roots")

    assert output_path == Path(
        "content/classical-roots/raw/classical-roots-vocabulary-from-classical-roots.pages.json"
    )


def test_generated_outputs_infer_category_from_raw_path() -> None:
    raw_path = Path("content/classical-roots/raw/classical-roots-source.pages.json")

    assert default_entries_output(raw_path) == Path(
        "content/classical-roots/normalized/classical-roots-source.entries.jsonl"
    )
    assert default_report_output(raw_path) == Path(
        "content/classical-roots/reports/classical-roots-source.validation.json"
    )
