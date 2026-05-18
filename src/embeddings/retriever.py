import os
import logging
from typing import List, Dict, Any, Optional
from neo4j import GraphDatabase
from src.env_utils import load_project_env

load_project_env()

logger = logging.getLogger(__name__)

class EmbeddingRetriever:
    """
    Handles retrieval of hierarchical legal text from Neo4j for embedding purposes.
    Concatenates Article + Clause + Point to provide full context for each leaf node.
    """
    def __init__(self, uri: Optional[str] = None, user: Optional[str] = None, password: Optional[str] = None):
        if uri:
            self.driver = GraphDatabase.driver(uri, auth=(user, password))
        else:
            self.driver = None

    def close(self):
        if self.driver:
            self.driver.close()

    def get_all_segments(self, doc_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Retrieves contextualized text for all leaf nodes in the database or a specific document.
        """
        if not self.driver:
            logger.error("Neo4j driver not initialized.")
            return []

        # Query to find Articles and their optional children (Clauses/Points)
        # We use hierarchical paths to ensure we capture nodes under Chapters/Sections.
        query = """
        MATCH (d:Document)
        """
        if doc_id:
            query += "WHERE d.id = $doc_id\n"
            
        query += """
        MATCH (d)-[:HAS_CHAPTER|HAS_SECTION|HAS_ARTICLE*..3]->(a:Article)
        OPTIONAL MATCH (a)-[:HAS_CLAUSE]->(c:Clause)
        OPTIONAL MATCH (c)-[:HAS_POINT]->(p:Point)
        RETURN 
            p.uid AS p_uid, c.uid AS c_uid, a.uid AS a_uid,
            p.clean_text AS p_txt, c.clean_text AS c_txt, a.clean_text AS a_txt,
            toInteger(a.index) AS a_idx, toInteger(c.index) AS c_idx, p.letter AS p_letter,
            d.id AS doc_id
        ORDER BY doc_id, a_idx, c_idx, p_letter
        """
        
        segments = []
        with self.driver.session() as session:
            result = session.run(query, doc_id=str(doc_id) if doc_id else None)
            for record in result:
                # Hierarchy-aware concatenation
                a_txt = (record["a_txt"] or "").strip()
                c_txt = (record["c_txt"] or "").strip()
                p_txt = (record["p_txt"] or "").strip()
                
                context_parts = [a_txt]
                if c_txt:
                    context_parts.append(c_txt)
                if p_txt:
                    context_parts.append(p_txt)
                
                full_text = "\n".join(context_parts)
                leaf_uid = record["p_uid"] or record["c_uid"] or record["a_uid"]
                
                segments.append({
                    "uid": leaf_uid,
                    "doc_id": record["doc_id"],
                    "text": full_text
                })

        # Deduplicate: If a Clause has Points, Cypher returns a row for each Point.
        # We only want the actual leaf node (the most specific level).
        # In our segments list, the specific Point entries will come after/before Article/Clause.
        # Because we want to embed EVERY level or only the LEAF level? 
        # Usually for RAG, we embed the most specific segments.
        
        seen_uids = set()
        unique_segments = []
        for seg in segments:
            if seg["uid"] not in seen_uids:
                unique_segments.append(seg)
                seen_uids.add(seg["uid"])
                
        return unique_segments

    def get_segment_context(self, uid: str) -> Optional[Dict[str, Any]]:
        """
        Return Document -> Article -> Clause -> Point context for any legal segment uid.
        """
        if not self.driver:
            logger.error("Neo4j driver not initialized.")
            return None

        query = """
        MATCH (node {uid: $uid})
        OPTIONAL MATCH (doc_a:Document)-[:HAS_ARTICLE]->(node)
        OPTIONAL MATCH (doc_ch:Document)-[:HAS_CHAPTER]->(:Chapter)-[:HAS_ARTICLE]->(node)
        OPTIONAL MATCH (article_for_clause:Article)-[:HAS_CLAUSE]->(node)
        OPTIONAL MATCH (doc_c1:Document)-[:HAS_ARTICLE]->(article_for_clause)
        OPTIONAL MATCH (doc_c2:Document)-[:HAS_CHAPTER]->(:Chapter)-[:HAS_ARTICLE]->(article_for_clause)
        OPTIONAL MATCH (clause_for_point:Clause)-[:HAS_POINT]->(node)
        OPTIONAL MATCH (article_for_point:Article)-[:HAS_CLAUSE]->(clause_for_point)
        OPTIONAL MATCH (doc_p1:Document)-[:HAS_ARTICLE]->(article_for_point)
        OPTIONAL MATCH (doc_p2:Document)-[:HAS_CHAPTER]->(:Chapter)-[:HAS_ARTICLE]->(article_for_point)
        WITH node, labels(node) AS labels,
             coalesce(doc_a, doc_ch, doc_c1, doc_c2, doc_p1, doc_p2) AS doc,
             coalesce(article_for_clause, article_for_point, CASE WHEN node:Article THEN node ELSE null END) AS article,
             coalesce(clause_for_point, CASE WHEN node:Clause THEN node ELSE null END) AS clause
        RETURN node, labels, doc, article, clause
        """
        with self.driver.session() as session:
            record = session.run(query, uid=uid).single()
            if not record:
                return None

        node = dict(record["node"])
        labels = list(record["labels"] or [])
        doc = dict(record["doc"]) if record["doc"] else {}
        article = dict(record["article"]) if record["article"] else {}
        clause = dict(record["clause"]) if record["clause"] else {}

        article_index = article.get("index", node.get("index") if "Article" in labels else None)
        clause_index = clause.get("index", node.get("index") if "Clause" in labels else None)
        point_letter = node.get("letter", "") if "Point" in labels else ""

        citation_parts = []
        if article_index:
            citation_parts.append(f"Điều {article_index}")
        if clause_index:
            citation_parts.append(f"khoản {clause_index}")
        if point_letter:
            citation_parts.append(f"điểm {point_letter}")
        if doc.get("title"):
            citation_parts.append(doc["title"])

        article_text = article.get("clean_text", node.get("clean_text", "") if "Article" in labels else "")
        clause_text = clause.get("clean_text", node.get("clean_text", "") if "Clause" in labels else "")
        point_text = node.get("clean_text", "") if "Point" in labels else ""
        text = "\n".join(part for part in [article_text, clause_text, point_text] if part)

        return {
            "uid": node.get("uid", uid),
            "labels": labels,
            "segment_type": node.get("segment_type") or next((l for l in ["Point", "Clause", "Article"] if l in labels), ""),
            "document_id": str(doc.get("id", "")),
            "document_title": doc.get("title", ""),
            "document_so_ky_hieu": doc.get("so_ky_hieu", ""),
            "document_type": doc.get("loai_van_ban", ""),
            "article_uid": article.get("uid", node.get("uid", "") if "Article" in labels else ""),
            "article_index": article_index,
            "article_title": article.get("title", node.get("title", "") if "Article" in labels else ""),
            "clause_uid": clause.get("uid", node.get("uid", "") if "Clause" in labels else ""),
            "clause_index": clause_index,
            "point_letter": point_letter,
            "text": text or node.get("clean_text") or node.get("text_content") or "",
            "display_citation": " ".join(citation_parts).strip() or uid,
        }
