from neo4j import GraphDatabase
import sys

def test_conn(password):
    uri = "bolt://127.0.0.1:7687"
    user = "neo4j"
    try:
        driver = GraphDatabase.driver(uri, auth=(user, password))
        with driver.session() as session:
            session.run("RETURN 1")
        print(f"SUCCESS: Mật khẩu '{password}' ĐÚNG.")
        return True
    except Exception as e:
        print(f"FAILED: Mật khẩu '{password}' SAI. Lỗi: {e}")
        return False

if __name__ == "__main__":
    if not test_conn("password123"):
        test_conn("password")
