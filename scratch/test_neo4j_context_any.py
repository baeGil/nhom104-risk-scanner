from neo4j import GraphDatabase

def test_waterfall():
    uri = "bolt://localhost:7687"
    driver = GraphDatabase.driver(uri, auth=("neo4j", "password"))
    
    query = """
    MATCH (a:Article)-[:HAS_CLAUSE]->(c:Clause)-[:HAS_POINT]->(p:Point)
    RETURN a.uid AS a_uid, a.clean_text AS a_txt, 
           c.uid AS c_uid, c.clean_text AS c_txt, 
           p.uid AS p_uid, p.clean_text AS p_txt
    LIMIT 1
    """
    with driver.session() as session:
        result = session.run(query)
        for record in result:
            print("="*40)
            print(f"[ARTICLE] {record['a_uid']}:\n{record['a_txt']}")
            print(f"[CLAUSE] {record['c_uid']}:\n{record['c_txt']}")
            print(f"[POINT] {record['p_uid']}:\n{record['p_txt']}")

if __name__ == "__main__":
    test_waterfall()
