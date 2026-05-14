from neo4j import GraphDatabase
import os

def check_apoc():
    uri = "bolt://localhost:7687"
    user = "neo4j"
    password = "password"
    try:
        driver = GraphDatabase.driver(uri, auth=(user, password))
        with driver.session() as session:
            result = session.run("RETURN apoc.version() as version")
            version = result.single()["version"]
            print(f"SUCCESS: APOC is active. Version: {version}")
    except Exception as e:
        print(f"FAILED: APOC is not active or error occurred: {e}")

if __name__ == "__main__":
    check_apoc()
