from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from .ids import DEFAULT_CATEGORY
from .paths import PipelinePaths


LESSON_TITLE_RE = re.compile(r"^\s*lesson\s+(\d+)\s*$", re.IGNORECASE | re.MULTILINE)
NUMBERED_WORD_RE = re.compile(r"^\s*(\d{1,2})\.\s*([A-Za-z][A-Za-z\-']+)\b", re.IGNORECASE)
USING_ROOT_CLUES_RE = re.compile(r"^\s*Using\s+ROOT\s+CLUES\s*$", re.IGNORECASE)
EXERCISE_HEAD_RE = re.compile(r"^\s*EXERCISE\s+([A-D])\s*:\s*(.+)$", re.IGNORECASE)
TXT_ROOT_RE = re.compile(r"([A-Z]{3,8})\s*\(from\s+the\s+Latin\s+word\s+([^\)]+)\)", re.IGNORECASE)


ROOT_TOPICS: dict[str, str] = {
    "GRAD": "taking steps forward in school",
    "SENS": "how we feel and notice things",
    "MOT": "movement and the energy that makes things go",
    "NUMER": "numbers and math ideas",
    "DELI": "pleasant and delightful experiences",
    "QUES": "asking thoughtful questions",
    "PART": "sharing pieces or roles in something bigger",
    "STUDI": "learning and staying focused on schoolwork",
    "SERV": "helping others and being useful",
    "VARI": "mixing different kinds of things",
    "EAS": "comfort and feeling relaxed",
    "FIN": "finishing and reaching the end",
    "FAMIL": "people and ideas that feel close and known",
    "SPECI": "special kinds or types",
    "ACT": "taking action and getting things done",
    "OFFIC": "important jobs that guide others",
    "CAPT": "taking hold of something",
    "STAT": "standing firm and sharing facts",
    "CLASS": "grouping things that belong together",
    "GRAT": "showing thanks and appreciation",
    "ORGAN": "parts that work together as a whole",
    "PROB": "testing ideas to find the truth",
    "LOC": "places and where things are",
    "TECHN": "practical skills and tools"
}

def _clean_line(line: str) -> str:
    line = line.replace("\u000c", " ")
    line = line.replace("\u2019", "'")
    line = re.sub(r"\s+", " ", line).strip()
    return line


STOPWORDS = {
    "the",
    "and",
    "with",
    "from",
    "that",
    "this",
    "your",
    "for",
    "are",
    "was",
    "were",
    "you",
    "his",
    "her",
    "their",
    "they",
    "into",
    "about",
    "word",
    "words",
    "root",
    "roots",
    "vocabulary",
    "classical",
}

SENSE_SPLIT_RE = re.compile(r"(adv\.|adj\.|n\.|v\.)\s*(\d\.)?\s*", re.IGNORECASE)


def _normalize_word_token(token: str) -> str:
    token = token.strip(" ,.;:()[]{}\t")
    token = token.lower()
    token = re.sub(r"[^a-z\-']", "", token)
    return token


def _dedupe_words(words: list[str]) -> list[str]:
    seen: set[str] = set()
    deduped: list[str] = []
    for word in words:
        normalized = _normalize_word_token(word)
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        deduped.append(normalized)
    return deduped


def _extract_lesson_windows_from_txt(raw_text: str) -> dict[int, str]:
    matches = list(LESSON_TITLE_RE.finditer(raw_text))
    windows: dict[int, str] = {}
    for i, m in enumerate(matches):
        num = int(m.group(1))
        if not (1 <= num <= 16):
            continue
        start = m.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(raw_text)
        windows[num] = raw_text[start:end]
    return windows


def _lesson_title_from_window(window: str, lesson_num: int) -> str:
    m = re.search(
        rf"lesson\s+{lesson_num}\s*:\s*([^\n]+)",
        window,
        re.IGNORECASE,
    )
    if not m:
        m = re.search(
            rf"Lesson\s+{lesson_num}\s*:\s*([^\n]+)",
            window,
            re.IGNORECASE,
        )
    if m:
        title = _clean_line(m.group(1))
        title = re.sub(r"\s+\d+$", "", title)
        return title
    return f"Lesson {lesson_num}"


def _looks_like_word_token(token: str) -> bool:
    w = _normalize_word_token(token)
    if not w:
        return False
    if len(w) < 3:
        return False
    if w in STOPWORDS:
        return False
    return True


def _extract_lesson_lists_with_markers(section_text: str) -> tuple[list[str], list[str], list[str]]:
    """Return ordered lists of key, familiar, and challenge words for a lesson."""

    lines = section_text.splitlines()
    normalized_lines = [_clean_line(line).lower() for line in lines]
    markers = {"key words", "familiar words", "challenge words"}

    def collect_key_words(start_idx: int) -> list[str]:
        words: list[str] = []
        for idx in range(start_idx + 1, len(lines)):
            raw_line = lines[idx]
            stripped = raw_line.strip()
            if not stripped:
                if words:
                    break
                continue
            cleaned = _clean_line(raw_line)
            lower = cleaned.lower()
            if any(lower.startswith(marker) for marker in markers) or lower.startswith("using root clues") or lower.startswith("lesson "):
                break
            for token in re.findall(r"[A-Za-z][A-Za-z\-']+", raw_line):
                normalized = _normalize_word_token(token)
                if normalized and normalized not in STOPWORDS:
                    words.append(normalized)
        return words

    def collect_single_word_list(start_idx: int) -> list[str]:
        words: list[str] = []
        seen_word = False
        for idx in range(start_idx + 1, len(lines)):
            raw_line = lines[idx]
            stripped = raw_line.strip()
            if not stripped:
                if seen_word:
                    break
                continue
            cleaned = _clean_line(raw_line)
            lower = cleaned.lower()
            if any(lower.startswith(marker) for marker in markers) and idx != start_idx + 1:
                break
            if lower.startswith("using root clues") or lower.startswith("lesson "):
                break
            if lower.startswith("with root"):
                continue
            if re.match(r"^[A-Z]{3,8}\s*\(from\s+the", cleaned):
                break
            tokens = re.findall(r"[A-Za-z][A-Za-z\-']+", raw_line)
            if tokens:
                first_token = tokens[0]
                start = raw_line.find(first_token)
                after_index = start + len(first_token)
                next_two = raw_line[after_index : after_index + 2]
                normalized = _normalize_word_token(first_token)
                first_non_space = raw_line.lstrip()
                if not first_non_space or not first_non_space[0].isalpha():
                    continue
                remaining_text = raw_line[after_index:].strip()
                if len(tokens) == 1 and remaining_text and next_two != "  ":
                    continue
                if _looks_like_word_token(normalized) and (len(tokens) == 1 or next_two == "  "):
                    words.append(normalized)
                    seen_word = True
                    continue
        return words

    key_words: list[str] = []
    for idx, value in enumerate(normalized_lines):
        if value.startswith("key words"):
            key_words = collect_key_words(idx)
            break

    familiar_words: list[str] = []
    challenge_words: list[str] = []
    for idx, value in enumerate(normalized_lines):
        if value.startswith("familiar words"):
            familiar_words.extend(collect_single_word_list(idx))
        elif value.startswith("challenge words"):
            challenge_words.extend(collect_single_word_list(idx))

    return (
        _dedupe_words(key_words),
        _dedupe_words(familiar_words),
        _dedupe_words(challenge_words),
    )


def _extract_word_senses(section_text: str, key_word: str) -> list[dict[str, str | None]]:
    pattern = re.compile(
        rf"(?ms)^\s*\d+\.\s*{re.escape(key_word)}\b[^\n]*\n(?P<body>.*?)(?=^\s*\d+\.\s*[A-Za-z]|^\s*[A-Z]{{3,8}}\s*\(from\s+the|\Z)"
    )
    match = pattern.search(section_text)
    if not match:
        return []

    cleaned_lines: list[str] = []
    for line in match.group("body").splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        lower = stripped.lower()
        if lower.startswith("familiar words") or lower.startswith("challenge words"):
            continue
        if lower.startswith("with root"):
            continue
        tokens = stripped.split()
        if len(tokens) == 1 and _looks_like_word_token(_normalize_word_token(tokens[0])):
            continue
        if lower.startswith("using root clues") or lower.startswith("lesson "):
            break
        cleaned_lines.append(stripped)

    body_text = " ".join(cleaned_lines)
    body_text = re.sub(r"\s+", " ", body_text).strip()
    if not body_text:
        return []

    senses: list[dict[str, str | None]] = []
    matches = list(SENSE_SPLIT_RE.finditer(body_text))
    if not matches:
        return []

    for idx, sense_match in enumerate(matches):
        start = sense_match.end()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(body_text)
        segment = body_text[start:end].strip()
        if not segment:
            continue
        segment = re.sub(r"^\d+\.\s*", "", segment)
        sentences = re.split(r"(?<=[.!?])\s+(?=[A-Z])", segment)
        definition = sentences[0].strip()
        example = " ".join(sentences[1:]).strip() if len(sentences) > 1 else ""
        example = re.sub(r"^\d+\.\s*", "", example)
        senses.append(
            {
                "part_of_speech": sense_match.group(1).lower(),
                "definition": definition,
                "example": example or None,
            }
        )

    return senses


def _word_type_for(word: str) -> str:
    lowered = word.lower()
    if lowered.endswith("ly"):
        return "adv."
    if lowered.endswith("ing"):
        return "n."
    if lowered.endswith("ed"):
        return "adj."
    if lowered.endswith((
        "tion",
        "sion",
        "ness",
        "ity",
        "ment",
        "tude",
        "ship",
        "ance",
        "ence",
        "acy",
        "hood",
        "dom",
        "er",
        "or",
        "ist",
    )):
        return "n."
    if lowered.endswith((
        "ful",
        "less",
        "ous",
        "ive",
        "able",
        "ible",
        "al",
        "ic",
        "ent",
        "ant",
        "ary",
        "ory",
    )):
        return "adj."
    if lowered.endswith(("ate", "fy", "ify", "ize", "ise", "en")):
        return "v."
    return "n."


def _match_root(word: str, lesson_roots: list[dict[str, Any]] | None) -> dict[str, Any] | None:
    if not lesson_roots:
        return None
    word_lower = word.lower()
    for root_info in lesson_roots:
        root_value = str(root_info.get("root") or "").lower()
        if not root_value:
            continue
        if word_lower.startswith(root_value) or root_value in word_lower:
            return root_info
    return None


def _extract_root_concept(root_info: dict[str, Any] | None) -> str:
    if not root_info:
        return "important ideas in daily life"
    meaning = str(root_info.get("meaning") or "")
    quoted = re.search(r"“([^”]+)”", meaning)
    if quoted:
        return quoted.group(1).strip()
    if "meaning" in meaning:
        after = meaning.split("meaning", 1)[-1].strip()
        if after:
            return after.strip(" :")
    return meaning or "important ideas in daily life"


def _root_topic(root_info: dict[str, Any] | None) -> str:
    if not root_info:
        return "important ideas in daily life"
    root_code = str(root_info.get("root") or "").upper()
    if root_code in ROOT_TOPICS:
        return ROOT_TOPICS[root_code]
    concept = _extract_root_concept(root_info)
    return concept if concept else "important ideas in daily life"


def _kid_friendly_definition(word: str, word_type: str, root_info: dict[str, Any] | None) -> str:
    topic = _root_topic(root_info)
    capitalized = word.capitalize()
    if word_type == "adv.":
        return f"{capitalized} tells us that something happens in a way related to {topic}."
    if word_type == "adj.":
        return f"{capitalized} describes something connected to {topic}."
    if word_type == "v.":
        return f"{capitalized} means taking action that involves {topic}."
    return f"{capitalized} is something we talk about when we think about {topic}."


def _kid_sentence(word: str, word_type: str, root_info: dict[str, Any] | None) -> str:
    topic = _root_topic(root_info)
    if word_type == "v.":
        return f"In class we {word} when we want to focus on {topic}."
    if word_type == "adj.":
        return f"The word {word} helps me describe things that are about {topic}."
    if word_type == "adv.":
        return f"It reminds me that something happens in a way that connects to {topic}."
    return f"In class, we say \"{word}\" when we talk about {topic}."


def _clean_example_text(example: str | None) -> str | None:
    if not example:
        return example
    cleaned = example.strip()
    for marker in ("VCR_", "Vocabulary From Classical Roots"):
        marker_index = cleaned.find(marker)
        if marker_index != -1:
            cleaned = cleaned[:marker_index].rstrip()
    noise_index = cleaned.find("  ")
    if noise_index != -1:
        cleaned = cleaned[:noise_index].rstrip()
    if cleaned and cleaned[-1] not in {".", "!", "?"}:
        cleaned = f"{cleaned}."
    return cleaned


def _extract_definition_and_example_from_block(block: str, key_word: str) -> tuple[str | None, str | None, str | None]:
    """Best-effort extraction of dictionary definition + example sentence.

    This uses the textbook dictionary-entry format inside the lesson block.
    Example shapes (from the book):
      1. gradually (...)\n        adv. Step-by-step...\n        Emma practiced...
    """

    text = block.replace("\r", "\n")

    # Grab the chunk after the numbered entry for `key_word`.
    # Stop when we hit the next numbered entry or the next root section.
    # Key words in dictionary listings are often followed by pronunciation in parentheses,
    # so we look for the line that begins with the entry number + key_word.
    pat = re.compile(
        rf"(?ms)^\s*\d+\.\s*{re.escape(key_word)}\b[^\n]*\n(?P<body>.*?)(?=^\s*\d+\.\s*[A-Za-z]|^\s*[A-Z]{{3,8}}\s*\(from\s+the|\Z)"
    )
    m = pat.search(text)
    if not m:
        return None, None, None

    body = m.group("body")
    # Collapse whitespace for sentence splitting.
    body = _clean_line(body)

    wt_match = re.search(r"\b(adv\.|adj\.|n\.|v\.)\b", body)
    word_type = wt_match.group(1) if wt_match else None

    body_wo_type = re.sub(r"\b(adv\.|adj\.|n\.|v\.)\b\s*", "", body, count=1)
    sentences = re.split(r"(?<=[.!?])\s+", body_wo_type)

    definition = sentences[0].strip() if sentences else None
    example_sentence = sentences[1].strip() if len(sentences) > 1 else None
    return definition, _clean_example_text(example_sentence), word_type


def _build_lesson_template(lesson_num: int, title: str) -> dict[str, Any]:
    return {
        "lesson_number": lesson_num,
        "title": title,
        "roots": [],
        "key_words": [],
        "familiar_words": [],
        "challenge_words": [],
        "word_details": [],
        "exercises": [],
    }


def _extract_exercises(section_text: str) -> list[dict[str, Any]]:
    exercises: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None

    for raw_line in section_text.splitlines():
        clean = _clean_line(raw_line.lstrip("= "))
        if not clean:
            continue
        if clean.startswith("VCR_"):
            continue
        if "Vocabulary From Classical Roots" in clean:
            continue
        if re.match(r"^[A-Z]{3,}\s*\(", clean):
            if current:
                exercises.append(current)
                current = None
            continue
        if clean.replace(" ", "").isdigit():
            continue
        if clean.lower().startswith("lesson "):
            continue

        if clean.startswith("Using ROOT CLUES"):
            if current:
                exercises.append(current)
            remainder = clean[len("Using ROOT CLUES") :].strip()
            current = {"title": "Using ROOT CLUES", "lines": []}
            if remainder:
                current["lines"].append(remainder)
            continue

        head_match = re.match(r"^(EXERCISE\s+[A-Z])\s*:\s*(.*)$", clean)
        if head_match:
            if current:
                exercises.append(current)
            current = {"title": head_match.group(1), "lines": []}
            remainder = head_match.group(2).strip()
            if remainder:
                current["lines"].append(remainder)
            continue

        if current:
            current["lines"].append(clean)

    if current:
        exercises.append(current)

    return exercises


def _build_word_details_from_lists(
    key_words: list[str], familiar_words: list[str], challenge_words: list[str]
) -> list[dict[str, Any]]:
    """Seed word detail entries before sense extraction.

    The structured output expects every listed word to include at least a
    fallback definition/example block. We capture the source list the word
    came from so downstream consumers can preserve grouping metadata.
    """

    details: list[dict[str, Any]] = []

    def append_words(words: list[str], group: str) -> None:
        for word in words:
            details.append(
                {
                    "word": word,
                    "group": group,
                    "senses": [],
                }
            )

    append_words(key_words, "key")
    append_words(familiar_words, "familiar")
    append_words(challenge_words, "challenge")
    return details


def _build_sections_from_pages(raw_payload: dict[str, Any]) -> list[dict[str, Any]]:
    pages = raw_payload.get("pages", [])
    source = raw_payload.get("source", {})
    category = str(source.get("category") or DEFAULT_CATEGORY)
    paths = PipelinePaths()
    debug_dir = paths.normalized_dir(category) / "debug"
    raw_text = "\n".join(str(p.get("text") or "") for p in pages)
    lesson_windows = _extract_lesson_windows_from_txt(raw_text)

    lessons = []
    for num in range(1, 17):
        section_text = lesson_windows.get(num, "")
        title = _lesson_title_from_window(section_text, num)
        lesson = _build_lesson_template(num, title)

        # Debug dump for Lesson 1 window to inspect whether slicing is correct.
        if num == 1:
            try:
                dbg_path = debug_dir / "lesson1_section.txt"
                dbg_path.parent.mkdir(parents=True, exist_ok=True)
                dbg_path.write_text(section_text, encoding="utf-8")
            except Exception:
                pass

        for root_m in TXT_ROOT_RE.finditer(section_text):
            root = root_m.group(1).upper()
            meaning_blob = _clean_line(root_m.group(2))
            example_word = re.sub(r"\W+", "", meaning_blob.split()[0].lower()) if meaning_blob else root.lower()
            lesson["roots"].append(
                {
                    "root": root,
                    "origin": "Latin/Greek",
                    "meaning": meaning_blob,
                    "example_word": example_word,
                }
            )

        lines = section_text.splitlines()
        start_idx = 0
        if lesson["roots"]:
            # find the line index after the last root
            for idx, line in enumerate(lines):
                if any(root['root'] in line.upper() for root in lesson["roots"]):
                    start_idx = idx + 1
                    break

        # Marker-based list extraction so we preserve the exact ordering
        # expected by the provided lesson templates.
        key_words, fam_words, ch_words = _extract_lesson_lists_with_markers(section_text)
        lesson["key_words"] = key_words[:24]
        lesson["familiar_words"] = fam_words[:24]
        lesson["challenge_words"] = ch_words[:24]

        lesson["word_details"] = _build_word_details_from_lists(
            lesson["key_words"],
            lesson["familiar_words"],
            lesson["challenge_words"],
        )

        if num == 1:
            try:
                (debug_dir / "lesson1_lists_dump.json").write_text(
                    json.dumps(
                        {
                            "key_words": lesson.get("key_words", []),
                            "familiar_words": lesson.get("familiar_words", []),
                            "challenge_words": lesson.get("challenge_words", []),
                            "word_details_preview": lesson.get("word_details", [])[:3],
                        },
                        ensure_ascii=False,
                        indent=2,
                    ),
                    encoding="utf-8",
                )
            except Exception:
                pass

        for detail in lesson.get("word_details", []):
            key_word = detail.get("word")
            if not key_word:
                continue
            senses = _extract_word_senses(section_text, key_word)
            if senses:
                for sense in senses:
                    if sense.get("example"):
                        sense["example"] = _clean_example_text(sense.get("example"))
                detail["senses"] = senses
            else:
                fallback_pos = _word_type_for(key_word)
                root_info = _match_root(key_word, lesson.get("roots", []))
                detail["senses"] = [
                    {
                        "part_of_speech": fallback_pos,
                        "definition": _kid_friendly_definition(key_word, fallback_pos, root_info),
                        "example": _kid_sentence(key_word, fallback_pos, root_info),
                    }
                ]

        lesson["exercises"] = _extract_exercises(section_text)
        lessons.append(lesson)

    # Ensure lessons 1..16
    by_num = {int(l["lesson_number"]): l for l in lessons}
    out: list[dict[str, Any]] = []
    for num in range(1, 17):
        out.append(by_num.get(num) or _build_lesson_template(num, f"Lesson {num}"))

    return out


def extract_lessons_from_text(raw_text: str) -> list[dict[str, Any]]:
    raise NotImplementedError("Use extract from raw pages JSON payload instead.")


def render_lessons_markdown(lessons: list[dict[str, Any]]) -> str:
    # Render Markdown to match the agent template format used by
    # content/<category>/normalized/lesson1_extraction_template.md.
    #
    # NOTE: This renderer currently uses the extracted fields already present
    # in `lesson` (roots/key_words/familiar_words/challenge_words/word_details/exercises).
    out: list[str] = ["# Vocabulary from Classical Roots: Grade 4", ""]
    for lesson in lessons:
        out.append(f"## Lesson {lesson['lesson_number']}: {lesson['title']}")
        out.append("")
        out.append("### 1. Words")
        out.append("#### Root Words")
        for root in lesson.get("roots", []):
            out.append(
                f"- {root['root']} (origin: {root['origin']}, meaning: {root['meaning']}, as in: {root['example_word']})"
            )
        out.append("")

        out.append("#### Key Words")
        out.extend([f"- {w}" for w in lesson.get("key_words", [])])
        out.append("")

        out.append("#### Familiar Words")
        out.extend([f"- {w}" for w in lesson.get("familiar_words", [])])
        out.append("")

        out.append("#### Challenge Words")
        out.extend([f"- {w}" for w in lesson.get("challenge_words", [])])
        out.append("")

        out.append("### 2. Explanation and Example Sentence for Each Word")
        for detail in lesson.get("word_details", []):
            out.append(f"- {detail['word']}")
            senses = detail.get("senses") or []
            if not senses:
                continue
            for sense in senses:
                part = sense.get("part_of_speech") or _word_type_for(detail["word"])
                definition = sense.get("definition") or ""
                out.append(f"  - ({part}): {definition}")
                example = sense.get("example")
                if example:
                    out.append(f"    - {example}")
        out.append("")

        out.append("### 4. Exercises")
        exercises = lesson.get("exercises", [])
        if exercises:
            for exercise in exercises:
                out.append(f"#### {exercise.get('title', 'Exercise')}")
                for line in exercise.get("lines", []):
                    out.append(f"- {line}")
                out.append("")
        else:
            out.append("- No exercises captured yet.")
            out.append("")
        # No explicit separator; template is per-lesson file.
    return "\n".join(out).rstrip() + "\n"


def extract_and_write_all_lessons(source_path: Path, json_output_path: Path, markdown_output_path: Path) -> dict[str, Any]:
    raw_payload = json.loads(source_path.read_text(encoding="utf-8"))
    lessons = _build_sections_from_pages(raw_payload)
    json_output_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_output_path.parent.mkdir(parents=True, exist_ok=True)

    json_output_path.write_text(json.dumps(lessons, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    markdown_output_path.write_text(render_lessons_markdown(lessons), encoding="utf-8")

    return {
        "source_path": str(source_path),
        "json_output_path": str(json_output_path),
        "markdown_output_path": str(markdown_output_path),
        "lesson_count": len(lessons),
    }


def _build_word_entries(lessons: list[dict[str, Any]], grade: int) -> list[dict[str, Any]]:
    """Transform lesson-centric data into a flat word-centric array.

    Each word entry is self-contained with all related info:
    - root info, definition, example, part of speech
    - related words (same root, same lesson)
    - exercises from the lesson
    """

    # Build lookup: word -> lesson info
    word_to_lesson: dict[str, dict[str, Any]] = {}
    word_to_root: dict[str, str] = {}
    root_to_words: dict[str, list[str]] = {}
    lesson_words: dict[int, list[str]] = {}

    for lesson in lessons:
        lesson_num = lesson.get("lesson_number", 0)
        roots = lesson.get("roots", [])
        all_words: list[str] = []

        for detail in lesson.get("word_details", []):
            word = detail.get("word", "")
            if not word:
                continue
            all_words.append(word)
            word_to_lesson[word] = lesson

            root_info = _match_root(word, roots)
            if root_info:
                root_code = str(root_info.get("root") or "").upper()
                word_to_root[word] = root_code
                root_to_words.setdefault(root_code, []).append(word)

        lesson_words[lesson_num] = all_words

    # Build word entries
    entries: list[dict[str, Any]] = []
    for lesson in lessons:
        lesson_num = lesson.get("lesson_number", 0)
        lesson_title = lesson.get("title", "")
        roots = lesson.get("roots", [])
        exercises = lesson.get("exercises", [])

        for detail in lesson.get("word_details", []):
            word = detail.get("word", "")
            if not word:
                continue

            group = detail.get("group", "key")
            senses = detail.get("senses", [])

            # Get root info
            root_code = word_to_root.get(word, "")
            root_info = None
            for r in roots:
                if r.get("root", "").upper() == root_code:
                    root_info = r
                    break

            # Get first sense
            part_of_speech = ""
            definition = ""
            example = ""
            if senses:
                first = senses[0]
                part_of_speech = first.get("part_of_speech", "")
                definition = first.get("definition", "")
                example = first.get("example") or ""

            # Related words
            same_root = [w for w in root_to_words.get(root_code, []) if w != word]
            same_lesson = [w for w in lesson_words.get(lesson_num, []) if w != word]

            entry = {
                "word": word,
                "grade": grade,
                "lesson_number": lesson_num,
                "lesson_title": lesson_title,
                "group": group,
                "root": root_code,
                "root_meaning": root_info.get("meaning", "") if root_info else "",
                "root_origin": root_info.get("origin", "") if root_info else "",
                "part_of_speech": part_of_speech,
                "definition": definition,
                "example": example,
                "related_words": {
                    "same_root": same_root,
                    "same_lesson": same_lesson,
                },
                "exercises": exercises,
            }
            entries.append(entry)

    return entries


def extract_and_write_words(
    source_path: Path,
    words_output_path: Path,
    grade: int,
) -> dict[str, Any]:
    """Load lesson bundle JSON and produce a word-centric words.json."""
    raw_payload = json.loads(source_path.read_text(encoding="utf-8"))
    lessons = _build_sections_from_pages(raw_payload)
    word_entries = _build_word_entries(lessons, grade=grade)

    words_output_path.parent.mkdir(parents=True, exist_ok=True)
    words_output_path.write_text(
        json.dumps(word_entries, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    return {
        "source_path": str(source_path),
        "words_output_path": str(words_output_path),
        "grade": grade,
        "word_count": len(word_entries),
    }