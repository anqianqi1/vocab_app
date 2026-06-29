"""Rewrite word definitions/examples into short, kid-friendly, distinct text.

Uses an Azure OpenAI chat deployment (default: DeepSeek-V4-Pro). Updates the
word-centric words.json in place. Default mode is a no-cost dry run.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

DEFAULT_API_VERSION = "2024-10-21"


def build_prompt(word: str, grade: int, part_of_speech: str) -> str:
    return (
        f"Define the word \"{word}\" ({part_of_speech}) for a grade-{grade} child. "
        "Use a short, friendly sentence a kid understands (max 14 words), no big words, "
        "do not start with the word itself. Then give one fun example sentence (max 12 words). "
        "Reply ONLY as JSON: {\"definition\": \"...\", \"example\": \"...\"}."
    )


def _client():
    endpoint = os.environ.get("AZURE_OPENAI_CHAT_ENDPOINT") or os.environ.get("AZURE_OPENAI_ENDPOINT")
    api_key = os.environ.get("AZURE_OPENAI_CHAT_KEY") or os.environ.get("AZURE_OPENAI_API_KEY")
    if not endpoint or not api_key:
        raise RuntimeError("Set AZURE_OPENAI_CHAT_ENDPOINT and AZURE_OPENAI_CHAT_KEY (or AZURE_OPENAI_* defaults).")
    # Azure AI Foundry v1 endpoint is OpenAI-compatible: use base_url, no api-version.
    if "/v1" in endpoint:
        from openai import OpenAI

        base = endpoint.split("/v1")[0] + "/v1"
        return OpenAI(base_url=base, api_key=api_key)
    from openai import AzureOpenAI

    version = os.environ.get("AZURE_OPENAI_API_VERSION", DEFAULT_API_VERSION)
    return AzureOpenAI(azure_endpoint=endpoint, api_key=api_key, api_version=version)


def _rewrite_one(client, deployment: str, word: str, grade: int, pos: str) -> dict[str, str]:
    resp = client.chat.completions.create(
        model=deployment,
        messages=[{"role": "user", "content": build_prompt(word, grade, pos)}],
        max_completion_tokens=300,
    )
    text = resp.choices[0].message.content or ""
    start, end = text.find("{"), text.rfind("}")
    data = json.loads(text[start : end + 1]) if start >= 0 and end > start else {}
    return {"definition": str(data.get("definition") or "").strip(), "example": str(data.get("example") or "").strip()}


def rewrite_definitions(words_path: Path, deployment: str | None = None, dry_run: bool = True, limit: int | None = None) -> dict[str, Any]:
    words = json.loads(words_path.read_text(encoding="utf-8"))
    dep = deployment or os.environ.get("AZURE_OPENAI_CHAT_DEPLOYMENT", "DeepSeek-V4-Pro")
    client = None if dry_run else _client()

    updated = 0
    failed: list[str] = []
    for i, w in enumerate(words):
        if limit is not None and i >= limit:
            break
        if not w.get("word"):
            continue
        if dry_run:
            continue
        try:
            r = _rewrite_one(client, dep, w["word"], int(w.get("grade") or 4), w.get("part_of_speech") or "")
            if r["definition"]:
                w["definition"] = r["definition"]
            if r["example"]:
                w["example"] = r["example"]
            updated += 1
            if updated % 10 == 0:
                words_path.write_text(json.dumps(words, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        except Exception as e:  # noqa: BLE001 - resilient batch
            failed.append(w.get("word", "?"))
            print(f"  ! {w.get('word')}: {e}")
    if not dry_run:
        words_path.write_text(json.dumps(words, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {"words_path": str(words_path), "deployment": dep, "dry_run": dry_run, "updated": updated, "failed": failed[:20]}
