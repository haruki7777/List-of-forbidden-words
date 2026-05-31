import json
import os
import re
import unicodedata
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_WORDS_PATH = BASE_DIR / "data" / "forbidden_words.ko.json"
RETURN_MATCH_VALUE = os.getenv("RETURN_MATCH_VALUE", "false").lower() == "true"

ZERO_WIDTH_PATTERN = re.compile(r"[\u200b\u200c\u200d\ufeff]")
SPACE_PATTERN = re.compile(r"\s+")
REPEATED_CHAR_PATTERN = re.compile(r"(.)\1{2,}")


@dataclass(frozen=True)
class ForbiddenRule:
    id: str
    type: str
    value: str
    category: str
    severity: int
    enabled: bool
    description: str = ""


def normalize_text(text: str, *, remove_spaces: bool = False) -> str:
    """Normalize user text before moderation checks."""
    if not isinstance(text, str):
        text = str(text)

    text = unicodedata.normalize("NFKC", text)
    text = ZERO_WIDTH_PATTERN.sub("", text)
    text = text.lower()
    text = REPEATED_CHAR_PATTERN.sub(r"\1\1", text)

    if remove_spaces:
        text = SPACE_PATTERN.sub("", text)
    else:
        text = SPACE_PATTERN.sub(" ", text).strip()

    return text


def mask_value(value: str) -> str:
    if not value:
        return ""
    if len(value) <= 2:
        return value[0] + "*"
    return value[0] + ("*" * (len(value) - 2)) + value[-1]


def _validate_rule(raw: dict[str, Any]) -> ForbiddenRule:
    rule_type = raw.get("type", "word")
    if rule_type not in {"word", "regex"}:
        raise ValueError(f"Invalid rule type: {rule_type}")

    return ForbiddenRule(
        id=str(raw["id"]),
        type=rule_type,
        value=str(raw["value"]),
        category=str(raw.get("category", "general")),
        severity=int(raw.get("severity", 1)),
        enabled=bool(raw.get("enabled", True)),
        description=str(raw.get("description", "")),
    )


@lru_cache(maxsize=1)
def load_rules() -> list[ForbiddenRule]:
    path = Path(os.getenv("FORBIDDEN_WORDS_PATH", str(DEFAULT_WORDS_PATH)))
    if not path.exists():
        raise FileNotFoundError(f"Forbidden words file not found: {path}")

    with path.open("r", encoding="utf-8") as f:
        payload = json.load(f)

    raw_rules = payload.get("rules", [])
    return [_validate_rule(rule) for rule in raw_rules if rule.get("enabled", True)]


def reload_rules() -> None:
    load_rules.cache_clear()


def check_text(text: str) -> dict[str, Any]:
    normalized = normalize_text(text)
    compact = normalize_text(text, remove_spaces=True)
    matches: list[dict[str, Any]] = []

    for rule in load_rules():
        if rule.type == "word":
            target = normalize_text(rule.value)
            target_compact = normalize_text(rule.value, remove_spaces=True)
            found = target in normalized or target_compact in compact
        else:
            try:
                found = re.search(rule.value, normalized, flags=re.IGNORECASE) is not None
            except re.error:
                found = False

        if found:
            display_value = rule.value if RETURN_MATCH_VALUE else mask_value(rule.value)
            matches.append(
                {
                    "id": rule.id,
                    "type": rule.type,
                    "value": display_value,
                    "category": rule.category,
                    "severity": rule.severity,
                    "description": rule.description,
                }
            )

    score = sum(item["severity"] for item in matches)
    return {
        "blocked": bool(matches),
        "score": score,
        "matches": matches,
        "normalized_text": normalized,
    }
