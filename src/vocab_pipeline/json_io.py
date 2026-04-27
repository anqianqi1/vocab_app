from __future__ import annotations

import json
from collections.abc import Iterable
from pathlib import Path
from typing import Any


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as file_handle:
        value = json.load(file_handle)
    if not isinstance(value, dict):
        raise ValueError(f"Expected JSON object in {path}")
    return value


def write_json(path: Path, payload: dict[str, Any]) -> None:
    ensure_parent(path)
    with path.open("w", encoding="utf-8") as file_handle:
        json.dump(payload, file_handle, ensure_ascii=False, indent=2)
        file_handle.write("\n")


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    if not path.exists():
        return records
    with path.open("r", encoding="utf-8") as file_handle:
        for line_number, line in enumerate(file_handle, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            value = json.loads(stripped)
            if not isinstance(value, dict):
                raise ValueError(f"Expected JSON object on {path}:{line_number}")
            records.append(value)
    return records


def write_jsonl(path: Path, records: Iterable[dict[str, Any]]) -> int:
    ensure_parent(path)
    count = 0
    with path.open("w", encoding="utf-8") as file_handle:
        for record in records:
            file_handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True))
            file_handle.write("\n")
            count += 1
    return count
