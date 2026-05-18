import os
from neo4j import GraphDatabase
from loguru import logger
from src.config import NEO4J_PASSWORD, NEO4J_URI, NEO4J_USER

class Neo4jSanitizer:
    def __init__(self, uri=None, user=None, password=None):
        self.uri = uri or NEO4J_URI
        self.user = user or NEO4J_USER
        self.password = password or NEO4J_PASSWORD
        self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))

    def clear_all(self):
        """Xóa sạch toàn bộ node và quan hệ trong Neo4j."""
        logger.warning(f"Đang xóa sạch database Neo4j tại {self.uri}...")
        try:
            with self.driver.session() as session:
                result = session.run("MATCH (n) DETACH DELETE n")
                summary = result.consume()
                nodes_deleted = summary.counters.nodes_deleted
                rels_deleted = summary.counters.relationships_deleted
                logger.success(f"Đã xóa {nodes_deleted} nodes và {rels_deleted} relationships.")
                return True
        except Exception as e:
            logger.error(f"Lỗi khi xóa database: {e}")
            return False
        finally:
            self.driver.close()

if __name__ == "__main__":
    # Test nhanh
    sanitizer = Neo4jSanitizer()
    sanitizer.clear_all()
