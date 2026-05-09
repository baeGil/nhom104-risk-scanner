"""
Validation & reporting for cross-reference extraction (T2.4).
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from neo4j import Driver

logger = logging.getLogger(__name__)


@dataclass
class ValidationReport:
    """Aggregate statistics produced by CrossReferenceValidator."""

    # ── Counts ──────────────────────────────────────────────────────────
    total_internal: int = 0
    resolved_internal: int = 0

    total_external: int = 0
    resolved_external_exact: int = 0
    resolved_external_fuzzy: int = 0
    unresolved_external: int = 0

    total_modification: int = 0
    resolved_modification: int = 0
    unresolved_modification: int = 0

    # ── Unresolved details (for manual review) ──────────────────────────
    unresolved_external_list: list[dict] = field(default_factory=list)
    unresolved_modification_list: list[dict] = field(default_factory=list)

    # ── Fuzzy confidence distribution ───────────────────────────────────
    fuzzy_confidence_buckets: dict[str, int] = field(default_factory=lambda: {
        "0.8-1.0": 0, "0.6-0.8": 0, "0.4-0.6": 0, "<0.4": 0,
    })

    # ── Derived metrics ─────────────────────────────────────────────────
    @property
    def external_resolution_rate(self) -> float:
        if self.total_external == 0:
            return 1.0
        return (self.resolved_external_exact + self.resolved_external_fuzzy) / self.total_external

    @property
    def modification_resolution_rate(self) -> float:
        if self.total_modification == 0:
            return 1.0
        return self.resolved_modification / self.total_modification

    def to_dict(self) -> dict:
        return {
            "internal": {
                "total": self.total_internal,
                "resolved": self.resolved_internal,
            },
            "external": {
                "total": self.total_external,
                "resolved_exact": self.resolved_external_exact,
                "resolved_fuzzy": self.resolved_external_fuzzy,
                "unresolved": self.unresolved_external,
                "resolution_rate": round(self.external_resolution_rate, 4),
            },
            "modification": {
                "total": self.total_modification,
                "resolved": self.resolved_modification,
                "unresolved": self.unresolved_modification,
                "resolution_rate": round(self.modification_resolution_rate, 4),
            },
            "fuzzy_confidence_distribution": self.fuzzy_confidence_buckets,
            "unresolved_external_sample": self.unresolved_external_list[:50],
            "unresolved_modification_sample": self.unresolved_modification_list[:50],
        }

    def save(self, path: str | Path) -> None:
        Path(path).write_text(json.dumps(self.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
        logger.info("Validation report saved to %s", path)

    def print_summary(self) -> None:
        print(
            f"\n{'='*60}\n"
            f"Cross-Reference Validation Report\n"
            f"{'='*60}\n"
            f"Internal refs  : {self.resolved_internal}/{self.total_internal}\n"
            f"External refs  : resolved {self.resolved_external_exact} exact + "
            f"{self.resolved_external_fuzzy} fuzzy / {self.total_external} total "
            f"({self.external_resolution_rate:.1%})\n"
            f"Modification   : {self.resolved_modification}/{self.total_modification} "
            f"({self.modification_resolution_rate:.1%})\n"
            f"{'='*60}\n"
            f"Targets: External ≥95%, Modification ≥95%\n"
        )


class CrossReferenceValidator:
    """
    Queries Neo4j to verify that extracted relationships point to valid nodes.

    Usage
    -----
        validator = CrossReferenceValidator(driver)
        report = validator.validate()
        report.print_summary()
        report.save("output/cross_ref_validation.json")
    """

    def __init__(self, driver: "Driver") -> None:
        self._driver = driver

    def validate(self) -> ValidationReport:
        """
        TODO (Team B — T2.4):
        Run validation queries against Neo4j and return a populated ValidationReport.

        Suggested Cypher queries:
        ─────────────────────────
        1. Count total [:REFERENCES_INTERNAL] vs those with valid targets:
           MATCH ()-[r:REFERENCES_INTERNAL]->() RETURN count(r)

        2. Count [:REFERENCES_EXTERNAL] by match_method:
           MATCH ()-[r:REFERENCES_EXTERNAL]->()
           RETURN r.match_method, count(r)

        3. Count unresolved (stored as separate UnresolvedRef nodes or in a log file):
           Depends on implementation choice in writer.py

        4. Check [:MODIFIES] where target Article exists:
           MATCH (s:Article)-[r:MODIFIES]->(t:Article) RETURN count(r)
        """
        raise NotImplementedError("T2.4: implement validate()")
