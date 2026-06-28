"""Image enrichment for word entries.

Generates or fetches one memory-aid image per word and records the image
filename back into the word-centric ``words.json`` bundle. Image files are
stored on disk and referenced by filename; the binary data is never stored in
the database. The default mode is a no-cost dry run that only reports the
prompts and target filenames that would be produced.
"""

from __future__ import annotations

import base64
import json
import os
import re
from pathlib import Path
from typing import Any

from .ids import normalize_category
from .paths import PipelinePaths

IMAGE_EXTENSION = "png"
DEFAULT_AZURE_API_VERSION = "2025-04-01-preview"


def slugify_word(word: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", word.strip().lower()).strip("-")
    return slug or "word"


def image_file_name(word: str, grade: int) -> str:
    return f"grade-{grade}_{slugify_word(word)}.{IMAGE_EXTENSION}"


def build_image_prompt(word_entry: dict[str, Any]) -> str:
    """Build a child-friendly illustration prompt for a single word."""
    word = word_entry.get("word") or ""
    part_of_speech = word_entry.get("part_of_speech") or ""
    definition = word_entry.get("definition") or ""
    pos_hint = f" ({part_of_speech})" if part_of_speech else ""
    return (
        f"A simple, friendly, colorful illustration for a children's vocabulary "
        f"flashcard that helps a student remember the word '{word}'{pos_hint}. "
        f"Meaning: {definition} "
        f"Show one clear, concrete, literal scene. Flat, clean, educational style. "
        f"No text, letters, or numbers anywhere in the image."
    )


def _write_image_from_response(response: Any, output_path: Path) -> None:
    """Persist the first image from an OpenAI/Azure images response to disk."""
    item = response.data[0]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    image_b64 = getattr(item, "b64_json", None)
    if image_b64:
        output_path.write_bytes(base64.b64decode(image_b64))
        return
    image_url = getattr(item, "url", None)
    if image_url:
        import urllib.request

        with urllib.request.urlopen(image_url) as remote:  # noqa: S310 - trusted provider URL
            output_path.write_bytes(remote.read())
        return
    raise RuntimeError("Image response did not include image data.")


def _generate_with_openai(prompt: str, output_path: Path) -> None:
    """Generate a single image via the public OpenAI Images API and write it to disk.

    Requires the ``OPENAI_API_KEY`` environment variable. Imported lazily so the
    rest of the pipeline never depends on network access.
    """
    from openai import OpenAI

    client = OpenAI()
    response = client.images.generate(
        model="gpt-image-1",
        prompt=prompt,
        size="1024x1024",
        n=1,
    )
    _write_image_from_response(response, output_path)


def _generate_with_azure_openai(prompt: str, output_path: Path, deployment: str | None = None) -> None:
    """Generate a single image via an Azure OpenAI / Azure AI Foundry image deployment.

    Reads configuration from environment variables:
        - AZURE_OPENAI_ENDPOINT          (e.g. https://<resource>.openai.azure.com)
        - AZURE_OPENAI_API_KEY
        - AZURE_OPENAI_IMAGE_DEPLOYMENT  (the deployment name; overridable via ``deployment``)
        - AZURE_OPENAI_API_VERSION       (optional; defaults to a recent preview)
    """
    from openai import AzureOpenAI

    endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT")
    api_key = os.environ.get("AZURE_OPENAI_API_KEY")
    resolved_deployment = deployment or os.environ.get("AZURE_OPENAI_IMAGE_DEPLOYMENT")
    api_version = os.environ.get("AZURE_OPENAI_API_VERSION", DEFAULT_AZURE_API_VERSION)

    missing = [
        name
        for name, value in (
            ("AZURE_OPENAI_ENDPOINT", endpoint),
            ("AZURE_OPENAI_API_KEY", api_key),
            ("AZURE_OPENAI_IMAGE_DEPLOYMENT (or --deployment)", resolved_deployment),
        )
        if not value
    ]
    if missing:
        raise RuntimeError("Missing Azure OpenAI configuration: " + ", ".join(missing))

    client = AzureOpenAI(azure_endpoint=endpoint, api_key=api_key, api_version=api_version)
    response = client.images.generate(
        model=resolved_deployment,
        prompt=prompt,
        size="1024x1024",
        n=1,
    )
    _write_image_from_response(response, output_path)


def enrich_words_with_images(
    words_path: Path,
    images_dir: Path | None = None,
    backend: str = "none",
    dry_run: bool = True,
    limit: int | None = None,
    category: str | None = None,
    deployment: str | None = None,
) -> dict[str, Any]:
    """Attach an image filename to each word entry in ``words_path``.

    backend:
        - "none": no image is produced (used for dry runs / planning).
        - "openai": generate an illustration per word via the public OpenAI Images API.
        - "azure": generate via an Azure OpenAI / Azure AI Foundry image deployment.
    dry_run:
        When True, no files are written and ``words.json`` is left unchanged; the
        function only reports the prompts and target filenames.
    """
    with words_path.open("r", encoding="utf-8") as file_handle:
        words = json.load(file_handle)
    if not isinstance(words, list):
        raise ValueError(f"Expected a JSON array in {words_path}")

    resolved_category = normalize_category(category) if category else None
    resolved_images_dir = images_dir or PipelinePaths().images_dir()

    planned: list[dict[str, str]] = []
    failed: list[dict[str, str]] = []
    generated = 0
    for index, word_entry in enumerate(words):
        if limit is not None and index >= limit:
            break
        word = word_entry.get("word") or ""
        if not word:
            continue
        grade = int(word_entry.get("grade") or 0)
        file_name = image_file_name(word, grade)
        prompt = build_image_prompt(word_entry)
        planned.append({"word": word, "file_name": file_name, "prompt": prompt})

        if dry_run:
            continue

        if backend == "none":
            word_entry["image"] = ""
            continue
        if backend not in ("openai", "azure"):
            raise ValueError(f"Unknown image backend: {backend}")

        output_path = resolved_images_dir / file_name
        try:
            if not output_path.exists():
                if backend == "openai":
                    _generate_with_openai(prompt, output_path)
                else:
                    _generate_with_azure_openai(prompt, output_path, deployment=deployment)
                generated += 1
            word_entry["image"] = file_name
            word_entry["image_source"] = (
                "openai:gpt-image-1"
                if backend == "openai"
                else f"azure:{deployment or os.environ.get('AZURE_OPENAI_IMAGE_DEPLOYMENT', 'gpt-image')}"
            )
        except Exception as error:  # noqa: BLE001 - keep a large batch resilient to one bad word
            failed.append({"word": word, "error": str(error)})
            print(f"  ! {word}: {error}")
            continue

        # Persist progress incrementally so a long run is resumable if interrupted.
        if generated % 10 == 0:
            words_path.write_text(
                json.dumps(words, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )

    if not dry_run and backend != "none":
        words_path.write_text(
            json.dumps(words, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    return {
        "words_path": str(words_path),
        "images_dir": str(resolved_images_dir),
        "backend": backend,
        "dry_run": dry_run,
        "category": resolved_category,
        "words_planned": len(planned),
        "images_generated": generated,
        "images_failed": len(failed),
        "failed": failed[:20],
        "sample": planned[:3],
    }
