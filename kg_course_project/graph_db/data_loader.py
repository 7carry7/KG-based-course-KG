# 将抽取的实体和关系写入数据库
def load_entities(conn, entities):
    """
    将实体批量加载到 Neo4j。
    使用 MERGE 确保幂等性。
    """
    # Neo4j 5.x+ 推荐使用 UNWIND + MERGE
    query = """
    UNWIND $entities AS entity
    MERGE (n {name: entity.name})
    ON CREATE SET n.created_at = timestamp()
    // 动态设置标签 (需要 APOC 库，如果不用APOC会复杂些)
    // 简化的方法：为每个标签单独执行
    """

    # 简化版：按标签分组加载 (无需 APOC)
    grouped_by_label = {}
    for e in entities:
        label = e['label']
        if label not in grouped_by_label:
            grouped_by_label[label] = []
        grouped_by_label[label].append(e)

    for label, entity_list in grouped_by_label.items():
        # :Label 必须是硬编码，不能作为参数
        query = f"""
        UNWIND $batch AS entity
        MERGE (n:{label} {{name: entity.name}})
        ON CREATE SET n.created_at = timestamp()
        """
        # 为了性能，可以分批 (batch)
        conn.execute_write(query, parameters={"batch": entity_list})


def load_relations(conn, relations):
    """
    将关系批量加载到 Neo4j。
    使用 MERGE 确保幂等性。
    """
    # 简化版：按类型分组加载 (无需 APOC)
    grouped_by_type = {}
    for r in relations:
        key = (r['head_label'], r['type'], r['tail_label'])
        if key not in grouped_by_type:
            grouped_by_type[key] = []
        grouped_by_type[key].append(r)

    for (head_label, rel_type, tail_label), batch in grouped_by_type.items():
        # :Label 和 :REL_TYPE 必须是硬编码
        query = f"""
        UNWIND $batch AS rel
        MATCH (h:{head_label} {{name: rel.head}})
        MATCH (t:{tail_label} {{name: rel.tail}})
        MERGE (h)-[r:{rel_type}]->(t)
        ON CREATE SET r.created_at = timestamp()
        """
        conn.execute_write(query, parameters={"batch": batch})