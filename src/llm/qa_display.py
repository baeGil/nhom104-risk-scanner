"""Rich terminal rendering helpers for the legal QA pipeline."""
from __future__ import annotations

from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from src.llm.models import IntentClassification
from src.llm.qa_models import QAAnswer, QARetrievalResult


class QARenderer:
    def __init__(self, console: Optional[Console] = None) -> None:
        self._console = console or Console()

    def render(
        self,
        message: str,
        classification: IntentClassification,
        retrieval: QARetrievalResult,
        answer: Optional[QAAnswer] = None,
    ) -> None:
        summary = Table.grid(expand=True)
        summary.add_column(ratio=1)
        summary.add_column(ratio=3)
        summary.add_row("Conversation", classification.conversation_id or "unknown")
        summary.add_row("Domain", classification.domain)
        summary.add_row("Confidence", f"{classification.confidence:.2f}")
        summary.add_row("Intents", ", ".join(intent.type for intent in classification.intents) or "[]")
        summary.add_row("Sub queries", str(len(classification.sub_queries)))
        summary.add_row("Retrieval", f"{retrieval.retrieval_status} ({len(retrieval.provisions)} provisions, {len(retrieval.errors)} errors)")
        summary.add_row("Message", message)
        self._console.print(Panel(summary, title="QA Summary", border_style="cyan"))

        if classification.sub_queries:
            sub_query_table = Table(title="Sub Queries", show_lines=True, expand=True)
            sub_query_table.add_column("#", style="bold cyan", width=3)
            sub_query_table.add_column("Intent", style="bold")
            sub_query_table.add_column("Strategy")
            sub_query_table.add_column("Rewritten Query")
            sub_query_table.add_column("Requires")
            for idx, sub_query in enumerate(classification.sub_queries, start=1):
                rewritten_query = retrieval.rewritten_queries.get(sub_query.query, sub_query.query)
                sub_query_table.add_row(
                    str(idx),
                    sub_query.intent,
                    sub_query.retrieval_strategy,
                    rewritten_query,
                    ", ".join(sub_query.requires) if sub_query.requires else "[]",
                )
            self._console.print(Panel(sub_query_table, border_style="bright_blue"))

        if retrieval.provisions:
            provision_table = Table(title="Retrieved Provisions", show_lines=True, expand=True)
            provision_table.add_column("#", style="bold cyan", width=3)
            provision_table.add_column("UID")
            provision_table.add_column("Citation")
            provision_table.add_column("Strategy")
            provision_table.add_column("Validity")
            for idx, provision in enumerate(retrieval.provisions, start=1):
                provision_table.add_row(
                    str(idx),
                    provision.uid or "-",
                    provision.display_citation or provision.article_title or "-",
                    provision.strategy or "-",
                    provision.validity.status,
                )
            self._console.print(Panel(provision_table, border_style="green"))

        if answer is not None:
            answer_table = Table.grid(expand=True)
            answer_table.add_column(ratio=1)
            answer_table.add_column(ratio=3)
            answer_table.add_row("Answer status", answer.retrieval_status)
            answer_table.add_row("Citations", str(len(answer.citations)))
            answer_table.add_row("Validity", answer.validity.status)
            answer_table.add_row(
                "Verified",
                str(bool(answer.citations) and all(citation.verified for citation in answer.citations)),
            )
            if answer.citations:
                answer_table.add_row(
                    "Citation UIDs",
                    ", ".join(citation.uid or citation.display_text for citation in answer.citations),
                )
            self._console.print(Panel(answer_table, title="Answer Summary", border_style="magenta"))
