"""Lightweight loader for config.yaml — single source of truth (NFR-MAINT-003).

Kept dependency-free (only PyYAML) so config can be imported from any module
without dragging in LangChain / Chroma / ML libs.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = PROJECT_ROOT / "config.yaml"


@lru_cache(maxsize=1)
def load_config() -> dict:
    with CONFIG_PATH.open(encoding="utf-8") as f:
        return yaml.safe_load(f)
