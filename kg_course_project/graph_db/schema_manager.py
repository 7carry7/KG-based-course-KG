# 创建约束和索引 (对应阶段1)
from kg_course_project.utils.file_io import read_yaml
import time


def clear_database(conn):
    """清空所有节点和关系 (危险操作)"""
    query_relations = "MATCH ()-[r]-() DELETE r"
    query_nodes = "MATCH (n) DELETE n"
    conn.run_query(query_relations)
    conn.run_query(query_nodes)


def apply_schema(conn, schema_path):
    """根据 schema.yaml 文件创建唯一性约束"""
    schema = read_yaml(schema_path)

    # 1. 创建节点约束
    for node in schema.get('nodes', []):
        label = node['label']
        # 假设我们总是为 'name' 属性创建约束
        if 'name' in node.get('properties', []):
            query = f"CREATE CONSTRAINT IF NOT EXISTS FOR (n:{label}) REQUIRE n.name IS UNIQUE"
            conn.run_query(query)
            print(f"已应用约束: {label}.name IS UNIQUE")

    # 2. (可选) 创建关系索引等...
    # ...

    # 等待约束生效
    time.sleep(1)