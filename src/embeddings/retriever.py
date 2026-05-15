import os
import logging
from typing import List, Dict, Any, Optional
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

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
