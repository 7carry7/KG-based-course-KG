# 智能问答 (NLU + Cypher)
def find_prerequisites(conn, concept_name):
    """
    (应用) 智能问答：查询一个知识点的前置知识

    我们利用图的递归查询能力，查找所有（直接和间接）的前置知识。
    """
    # REQUIRES_PRE* 查找 1 层或多层的前置关系
    query = """
    MATCH (c:Concept {name: $name})-[r:REQUIRES_PRE*]->(pre:Concept)
    RETURN pre.name AS prerequisite
    """

    try:
        results = conn.run_query(query, parameters={"name": concept_name})
        prereqs = [record["prerequisite"] for record in results]
        return list(set(prereqs))  # 去重
    except Exception as e:
        print(f"QA 查询错误: {e}")
        return []