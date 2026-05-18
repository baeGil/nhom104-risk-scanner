"""
Execution pipeline for Segmentation & Ingest (Phase 1)
T1.3, T1.5, T1.6
"""
import json
import logging
import os
from typing import Iterator

from neo4j import GraphDatabase

from src.config import EMBED_SERVICE_URL, NEO4J_PASSWORD, NEO4J_URI, NEO4J_USER

from .models import ParseResult
from .parser import LegalDocumentParser
from .confidence import ConfidenceScorer
from .writer import SegmentWriter
from .embedder import ArticleEmbedder

logger = logging.getLogger(__name__)

class SegmentationPipeline:
    def __init__(
        self,
        metadata_path: str,
        content_path: str,
        neo4j_uri: str = NEO4J_URI,
        neo4j_user: str = NEO4J_USER,
        neo4j_password: str = NEO4J_PASSWORD,
        embed_service_url: str = EMBED_SERVICE_URL,
    ):
        self.metadata_path = metadata_path
        self.content_path = content_path
        self.driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))
        self.parser = LegalDocumentParser()
        self.scorer = ConfidenceScorer()
        self.writer = SegmentWriter(self.driver)
        self.embedder = ArticleEmbedder(self.driver, embed_service_url=embed_service_url)
        
    def _load_metadata(self) -> dict[str, dict]:
        """Load Metadata into RAM dictionary (Option 1)"""
        logger.info(f"Loading metadata from {self.metadata_path}...")
        metadata = {}
        with open(self.metadata_path, "r", encoding="utf-8") as f:
            # Assuming JSONL format for metadata
            for line in f:
                if not line.strip():
                    continue
                try:
                    record = json.loads(line)
                    doc_id = str(record.get("id", record.get("doc_id")))
                    metadata[doc_id] = record
                except Exception as exc:
                    logger.warning("Error parsing metadata line: %s", exc)
        logger.info(f"Loaded {len(metadata)} metadata records.")
        return metadata

    def _stream_content(self, metadata: dict[str, dict]) -> Iterator[dict]:
        """Stream content file and join with metadata"""
        logger.info(f"Streaming content from {self.content_path}...")
        with open(self.content_path, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    record = json.loads(line)
                    doc_id = str(record.get("id", record.get("doc_id")))
                    meta = metadata.get(doc_id, {})
                    yield {
                        "doc_id": doc_id,
                        "clean_html": record.get("clean_html", record.get("html", "")),
                        "expected_article_count": meta.get("article_count"),
                        "loai_van_ban": meta.get("loai_van_ban", "")
                    }
                except Exception as exc:
                    logger.warning("Error parsing content line: %s", exc)

    def run_parser_and_ingest(self):
        """Parse all documents and ingest to Neo4j"""
        metadata = self._load_metadata()
        
        batch_results = []
        batch_size = 100
        total_docs = 0
        
        for doc in self._stream_content(metadata):
            try:
                # 1. Parse
                result = self.parser.parse(
                    doc_id=doc["doc_id"],
                    clean_html=doc["clean_html"],
                    loai_van_ban=doc["loai_van_ban"]
                )
                
                # 2. Score
                result = self.scorer.score(
                    result,
                    expected_article_count=doc["expected_article_count"]
                )
                
                batch_results.append(result)
                total_docs += 1
                
                # 3. Batch Ingest
                if len(batch_results) >= batch_size:
                    self.scorer.score_batch(batch_results) # for logging distribution
                    self.writer.write_batch(batch_results)
                    batch_results = []
                    logger.info(f"Processed {total_docs} documents...")
                    
            except Exception as exc:
                logger.error(f"Failed to process doc {doc.get('doc_id')}: {exc}")
                
        # Process remaining
        if batch_results:
            self.scorer.score_batch(batch_results)
            self.writer.write_batch(batch_results)
            logger.info(f"Processed {total_docs} documents in total.")
            
    def run_embedding(self):
        """Generate embeddings for all articles"""
        logger.info("Starting embedding generation...")
        stats = self.embedder.embed_all(overwrite=False)
        logger.info(f"Embedding stats: {stats}")

    def close(self):
        self.writer.close()
        self.driver.close()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    pipeline = SegmentationPipeline(
        metadata_path="data/metadata.jsonl",
        content_path="data/content.jsonl"
    )
    pipeline.run_parser_and_ingest()
    pipeline.run_embedding()
    pipeline.close()
