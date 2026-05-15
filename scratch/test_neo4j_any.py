from neo4j import GraphDatabase
uri = "bolt://localhost:7687"
driver = GraphDatabase.driver(uri, auth=("neo4j", "password"))
with driver.session() as session:
    res = session.run("MATCH (a:Article) RETURN a.uid, a.clean_text LIMIT 1").single()
    if res: print(f"Found: {res['a.uid']}\n{res['a.clean_text'][:200]}")
    else: print("No Articles found!")
