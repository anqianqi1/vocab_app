from __future__ import annotations

import hashlib
import re
from pathlib import Path


DEFAULT_CATEGORY = "uncategorized"


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip().lower()).strip("-")
    return slug or "source"


def normalize_category(category: str | None) -> str:
    if not category:
        return DEFAULT_CATEGORY
    return slugify(category)


def source_id_from_path(path: Path, category: str | None = None) -> str:
    source_slug = slugify(path.stem)
    category_slug = normalize_category(category)
    if category_slug == DEFAULT_CATEGORY:
        return source_slug
    return f"{category_slug}-{source_slug}"


def normalize_term(term: str) -> str:
    return re.sub(r"\s+", " ", term.strip().casefold())


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file_handle:
        for chunk in iter(lambda: file_handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def stable_entry_id(source_id: str, source_page: int, source_order: int, term: str) -> str:
    base = f"{source_id}:{source_page}:{source_order}:{normalize_term(term)}"
    return hashlib.sha1(base.encode("utf-8")).hexdigest()[:16]
