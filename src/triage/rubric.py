from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

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
            "go", "golang", "python", "php", "laravel", "symfony",
            "fastapi", "claude", "anthropic", "openai", "llm", "rag",
            "embedding", "vector", "clickhouse", "postgres", "postgresql",
            "kafka", "redis", "docker", "microservice", "api", "backend",
            "mcp", "sentence-transformers", "faiss", "onnx",
        ]
    )

    blocklist: list[str] = field(
        default_factory=lambda: [
            "wordpress", "drupal", "joomla", "magento", "shopify",
            "wix", "webflow", "elementor", "prestashop", "opencart",
            "squarespace", "godaddy", "bitrix",
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
        if path is None:
            return cls()
        data = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
        known = {f for f in cls.__dataclass_fields__}
        unknown = set(data) - known
        if unknown:
            raise ValueError(f"unknown rubric keys: {sorted(unknown)}")
        return cls(**data)
