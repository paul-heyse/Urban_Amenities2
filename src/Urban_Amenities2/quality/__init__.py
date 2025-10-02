"""Quality scoring and brand deduplication utilities."""

from .dedupe import BrandDedupeConfig, apply_brand_dedupe
from .scoring import (
    HOURS_BONUS_MAP,
    QualityScorer,
    QualityScoringConfig,
    build_scoring_config,
    summarize_quality,
)

__all__ = [
    "HOURS_BONUS_MAP",
    "QualityScorer",
    "QualityScoringConfig",
    "build_scoring_config",
    "summarize_quality",
    "BrandDedupeConfig",
    "apply_brand_dedupe",
]
