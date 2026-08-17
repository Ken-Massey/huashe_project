"""Historical incoming-letter/reply database and matching utilities."""

from .database import (
    build_history_database,
    history_database_stats,
    load_history_cases,
    set_history_case_active,
)
from .matcher import match_similar_replies

__all__ = [
    "build_history_database",
    "history_database_stats",
    "load_history_cases",
    "set_history_case_active",
    "match_similar_replies",
]
