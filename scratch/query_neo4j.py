from neo4j import GraphDatabase
driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "password"))
def get_node(uid):
    with driver.session() as session:
        res = session.run("MATCH (n) WHERE n.uid = $uid RETURN labels(n)[0] as lbl, n.text_content as txt LIMIT 1", uid=uid).single()
        if res: print(f"[{res['lbl']}] {uid}: {res['txt'][:100]}...")
get_node("doc_153913_dieu_1")
get_node("doc_153913_dieu_1_khoan_1")
get_node("doc_153913_dieu_1_khoan_1_diem_a")
driver.close()
