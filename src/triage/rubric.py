"""The scoring rubric: thresholds, weights, and the skill/blocklist words.

Everything tunable lives here so the yaml can change behaviour without code
changes. Loaded from config/rubric.yaml; falls back to these defaults.
"""

from __future__ import annotations

from dataclasses import dataclass, field, fields
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class Rubric:
    min_spend: float = 1000.0
    min_hire_rate: float = 0.5
    max_proposals: int = 15
    max_age_minutes: int = 360
    min_hourly: float = 25.0
    min_fixed: float = 300.0
    require_payment_verified: bool = True

    skills: list[str] = field(
        default_factory=lambda: [
            "go",
            "golang",
            "python",
            "php",
            "laravel",
            "symfony",
            "fastapi",
            "claude",
            "anthropic",
            "openai",
            "llm",
            "rag",
            "embedding",
            "vector",
            "clickhouse",
            "postgres",
            "postgresql",
            "kafka",
            "redis",
            "docker",
            "microservice",
            "api",
            "backend",
            "mcp",
            "sentence-transformers",
            "faiss",
            "onnx",
        ]
    )

    blocklist: list[str] = field(
        default_factory=lambda: [
            "wordpress",
            "drupal",
            "joomla",
            "magento",
            "shopify",
            "wix",
            "webflow",
            "elementor",
            "prestashop",
            "opencart",
            "squarespace",
            "godaddy",
            "bitrix",
        ]
    )

    target_hourly: float = 55.0

    w_skill: int = 35
    w_client: int = 25
    w_competition: int = 20
    w_recency: int = 10
    w_budget: int = 10

    @classmethod
    def load(cls, path: str | Path | None) -> Rubric:
        """Read a rubric yaml (or defaults if path is None), type-checked.

        Raises ValueError on unknown keys or a value of the wrong type, so a
        bad config blows up here with a readable message instead of much later
        with a TypeError from deep inside the scorer.
        """
        if path is None:
            return cls()
        data = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
        if not isinstance(data, dict):
            raise ValueError("rubric yaml must be a mapping at the top level")

        types = {f.name: f.type for f in fields(cls)}
        unknown = set(data) - set(types)
        if unknown:
            raise ValueError(f"unknown rubric keys: {sorted(unknown)}")

        clean = {key: _coerce(key, value, types[key]) for key, value in data.items()}
        return cls(**clean)


# Map the (stringified) field annotations to a runtime validator/coercer.
def _coerce(key: str, value: Any, annotation: Any) -> Any:
    ann = str(annotation)
    if ann == "bool":
        if not isinstance(value, bool):
            raise ValueError(f"{key}: expected true/false, got {value!r}")
        return value
    if ann == "int":
        # bool is a subclass of int; reject it so max_proposals: true fails.
        if isinstance(value, bool) or not isinstance(value, int):
            raise ValueError(f"{key}: expected an integer, got {value!r}")
        return value
    if ann == "float":
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError(f"{key}: expected a number, got {value!r}")
        return float(value)
    if ann.startswith("list"):
        if not isinstance(value, list) or not all(isinstance(x, str) for x in value):
            raise ValueError(f"{key}: expected a list of strings, got {value!r}")
        return value
    return value
