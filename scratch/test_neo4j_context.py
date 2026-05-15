from neo4j import GraphDatabase

def test_waterfall():
    uri = "bolt://localhost:7687"
    driver = GraphDatabase.driver(uri, auth=("neo4j", "password"))
    
    query = """
    MATCH (d:Document {id: '153913'})-[:HAS_ARTICLE]->(a:Article)
    OPTIONAL MATCH (a)-[:HAS_CLAUSE]->(c:Clause)
    OPTIONAL MATCH (c)-[:HAS_POINT]->(p:Point)
    RETURN a.uid AS a_uid, a.clean_text AS a_txt, 
           c.uid AS c_uid, c.clean_text AS c_txt, 
           p.uid AS p_uid, p.clean_text AS p_txt
    ORDER BY a.index, c.index, p.letter
    LIMIT 3
    """
    with driver.session() as session:
        result = session.run(query)
        for record in result:
            print("="*40)
            print(f"[ARTICLE] {record['a_uid']}:\n{record['a_txt']}")
            if record['c_uid']:
                print(f"[CLAUSE] {record['c_uid']}:\n{record['c_txt']}")
            if record['p_uid']:
                print(f"[POINT] {record['p_uid']}:\n{record['p_txt']}")

if __name__ == "__main__":
    test_waterfall()
