"""
LegalSegment index setup for Task 4 hybrid retrieval.

This module prepares the Neo4j retrieval surface used by contract review:
- labels embedded Article, Clause, and Point nodes as LegalSegment
- creates vector and full-text indexes for LegalSegment search
- validates labels, indexes, embedding counts, and dimensions

Usage:
    python -m src.data_pipeline.legal_segment_index apply
    python -m src.data_pipeline.legal_segment_index validate
"""
from __future__ import annotations

import argparse
import logging
from dataclasses import dataclass
from typing import Any

from neo4j import GraphDatabase

from src.config import EMBED_DIMENSIONS, NEO4J_URI, neo4j_auth

logger = logging.getLogger(__name__)

LEGAL_SEGMENT_VECTOR_INDEX = "legal_segment_embeddings"
LEGAL_SEGMENT_FULLTEXT_INDEX = "legal_segment_fulltext"
DOCUMENT_TITLE_FULLTEXT_INDEX = "document_title_fulltext"


@dataclass
class ValidationReport:
    legal_segment_count: int
    embedded_by_label: list[dict[str, Any]]
    sample_dimensions: list[dict[str, Any]]
    indexes: list[dict[str, Any]]
    missing_indexes: list[str]
    missing_legal_segment_labels: int

    @property
    def ok(self) -> bool:
        return not self.missing_indexes and self.missing_legal_segment_labels == 0


class LegalSegmentIndexManager:
    def __init__(self, uri: str = NEO4J_URI, auth: tuple[str, str] | None = None) -> None:
        self._driver = GraphDatabase.driver(uri, auth=auth or neo4j_auth())

    def close(self) -> None:
        self._driver.close()

    def apply(self) -> ValidationReport:
        """Apply labels and indexes, then return validation report."""
        with self._driver.session() as session:
            result = session.run(
                """
                MATCH (n)
                WHERE (n:Article OR n:Clause OR n:Point)
                  AND n.uid IS NOT NULL
                  AND n.embedding IS NOT NULL
                SET n:LegalSegment
                SET n.segment_type =
                  CASE
                    WHEN n:Point THEN 'Point'
                    WHEN n:Clause THEN 'Clause'
                    WHEN n:Article THEN 'Article'
                    ELSE coalesce(n.segment_type, 'LegalSegment')
                  END
                RETURN count(n) AS labeled
                """
            )
            labeled = result.single()["labeled"]
            logger.info("Labeled %s embedded nodes as LegalSegment", labeled)

            self._create_indexes(session)

        return self.validate()

    def validate(self) -> ValidationReport:
        with self._driver.session() as session:
            legal_segment_count = session.run(
                "MATCH (n:LegalSegment) RETURN count(n) AS count"
            ).single()["count"]

            embedded_by_label = [
                dict(row)
                for row in session.run(
                    """
                    MATCH (n)
                    WHERE n.embedding IS NOT NULL
                    RETURN labels(n) AS labels, count(n) AS count
                    ORDER BY count DESC
                    """
                )
            ]

            sample_dimensions = [
                dict(row)
                for row in session.run(
                    """
                    MATCH (n:LegalSegment)
                    WHERE n.embedding IS NOT NULL
                    RETURN labels(n) AS labels, n.uid AS uid, size(n.embedding) AS dimensions
                    LIMIT 10
                    """
                )
            ]

            indexes = [
                dict(row)
                for row in session.run(
                    """
                    SHOW INDEXES
                    YIELD name, type, entityType, labelsOrTypes, properties, state
                    RETURN name, type, entityType, labelsOrTypes, properties, state
                    ORDER BY name
                    """
                )
            ]

            missing_legal_segment_labels = session.run(
                """
                MATCH (n)
                WHERE (n:Article OR n:Clause OR n:Point)
                  AND n.uid IS NOT NULL
                  AND n.embedding IS NOT NULL
                  AND NOT n:LegalSegment
                RETURN count(n) AS count
                """
            ).single()["count"]

        existing_index_names = {idx["name"] for idx in indexes}
        required_indexes = {
            LEGAL_SEGMENT_VECTOR_INDEX,
            LEGAL_SEGMENT_FULLTEXT_INDEX,
            DOCUMENT_TITLE_FULLTEXT_INDEX,
        }

        return ValidationReport(
            legal_segment_count=legal_segment_count,
            embedded_by_label=embedded_by_label,
            sample_dimensions=sample_dimensions,
            indexes=indexes,
            missing_indexes=sorted(required_indexes - existing_index_names),
            missing_legal_segment_labels=missing_legal_segment_labels,
        )

    def _create_indexes(self, session) -> None:
        session.run(
            f"""
            CREATE VECTOR INDEX {LEGAL_SEGMENT_VECTOR_INDEX}
            IF NOT EXISTS
            FOR (n:LegalSegment)
            ON n.embedding
            OPTIONS {{
              indexConfig: {{
                `vector.dimensions`: $dimensions,
                `vector.similarity_function`: 'cosine'
              }}
            }}
            """,
            dimensions=EMBED_DIMENSIONS,
        )
        session.run(
            f"""
            CREATE FULLTEXT INDEX {LEGAL_SEGMENT_FULLTEXT_INDEX}
            IF NOT EXISTS
            FOR (n:LegalSegment)
            ON EACH [n.clean_text, n.text_content, n.title]
            """
        )
        session.run(
            f"""
            CREATE FULLTEXT INDEX {DOCUMENT_TITLE_FULLTEXT_INDEX}
            IF NOT EXISTS
            FOR (d:Document)
            ON EACH [d.title, d.so_ky_hieu, d.normalized_so_ky_hieu]
            """
        )
        logger.info("Requested LegalSegment vector and full-text indexes")


def print_report(report: ValidationReport) -> None:
    print("LegalSegment validation")
    print(f"- legal_segment_count: {report.legal_segment_count}")
    print(f"- missing_legal_segment_labels: {report.missing_legal_segment_labels}")
    print(f"- missing_indexes: {report.missing_indexes or 'none'}")
    print("- embedded_by_label:")
    for row in report.embedded_by_label:
        print(f"  - {row}")
    print("- sample_dimensions:")
    for row in report.sample_dimensions:
        print(f"  - {row}")
    print("- indexes:")
    for idx in report.indexes:
        if idx["name"] in {
            LEGAL_SEGMENT_VECTOR_INDEX,
            LEGAL_SEGMENT_FULLTEXT_INDEX,
            DOCUMENT_TITLE_FULLTEXT_INDEX,
        }:
            print(f"  - {idx}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Manage LegalSegment retrieval indexes")
    parser.add_argument("command", choices=["apply", "validate"])
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s - %(message)s")

    manager = LegalSegmentIndexManager()
    try:
        report = manager.apply() if args.command == "apply" else manager.validate()
        print_report(report)
        return 0 if report.ok else 1
    finally:
        manager.close()


if __name__ == "__main__":
    raise SystemExit(main())
