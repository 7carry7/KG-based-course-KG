# 运行整个数据处理和图谱构建流程的主脚本
import configparser
from kg_course_project.graph_db.connection import Neo4jConnection
from kg_course_project.graph_db import schema_manager, data_loader
from kg_course_project.data_acquisition import data_cleaner
from kg_course_project.extraction import ner, re
import os


def main_pipeline():
    print("--- 知识图谱构建流程启动 ---")

    # 1. 加载配置
    config = configparser.ConfigParser()
    config.read('config.ini')

    neo4j_uri = config['NEO4J']['URI']
    neo4j_auth = (config['NEO4J']['USER'], config['NEO4J']['PASSWORD'])
    schema_path = config['PATHS']['SCHEMA_FILE']
    raw_data_dir = config['PATHS']['RAW_DATA_DIR']

    # 2. 初始化数据库连接
    db_conn = Neo4jConnection(uri=neo4j_uri, auth=neo4j_auth)

    try:
        # 3. 清理数据库并设置模式 (约束)
        print("\n[阶段1: 设置数据库模式]")
        schema_manager.clear_database(db_conn)
        print("数据库已清空。")
        schema_manager.apply_schema(db_conn, schema_path)
        print("模式和约束已应用。")

        # 4. 数据获取和清洗 (MVP: 从本地txt读取)
        print("\n[阶段2.1: 数据获取与清洗]")
        # 我们在这里模拟，只读取一个文件
        mock_data_file = os.path.join(raw_data_dir, 'course_content.txt')
        try:
            with open(mock_data_file, 'r', encoding='utf-8') as f:
                raw_text = f.read()
            print(f"成功读取模拟数据: {mock_data_file}")
        except FileNotFoundError:
            print(f"错误: 未找到模拟数据文件: {mock_data_file}")
            print("请按照 README.md 中的指示创建该文件。")
            return

        cleaned_text = data_cleaner.simple_clean(raw_text)

        # 5. 知识抽取 (MVP: 基于规则)
        print("\n[阶段2.2: 知识抽取]")

        # 5a. 实体识别 (NER)
        # 定义我们的领域词典 (这是MVP的核心)
        domain_vocab = {
            "Concept": ["RDF", "RDFS", "OWL", "知识表示", "知识抽取", "实体识别", "关系抽取", "知识存储"],
            "Technology": ["Neo4j", "spaCy"],
            "Algorithm": ["BERT"],
            "Chapter": ["第一章", "第二章", "第三章"]
        }
        entities = ner.extract_entities_by_vocab(cleaned_text, domain_vocab)
        print(f"抽取到实体: {len(entities)} 个")

        # 5b. 关系抽取 (RE)
        # 定义我们的规则 (MVP)
        rules = [
            # 规则1: (A 是 B 的基础) -> (B REQUIRES_PRE A)
            (r'([\w\s]+)\s+是\s+([\w\s]+)\s+的\s+基础', 'REQUIRES_PRE', 2, 1),
            # 规则2: (A 需要 B) -> (A REQUIRES_PRE B)
            (r'([\w\s]+)\s+需要\s+([\w\s]+)', 'REQUIRES_PRE', 1, 2),
            # 规则3: (A 使用 B 技术) -> (A USES_TECH B)
            (r'([\w\s]+)\s+使用\s+([\w\s]+)\s+技术', 'USES_TECH', 1, 2),
            # 规则4: (A 使用 B 算法) -> (A APPLIES_ALGO B)
            (r'([\w\s]+)\s+使用\s+([\w\s]+)\s+算法', 'APPLIES_ALGO', 1, 2),
            # 规则5: (A章 包含...: B, C) -> (A INCLUDES_CONCEPT B), (A INCLUDES_CONCEPT C)
            (r'([\w\s]+)：\s*本章包含的概念有：([\w\s，]+)', 'INCLUDES_CONCEPT', 1, 2)
        ]

        relations = re.extract_relations_by_rules(cleaned_text, entities, rules)
        print(f"抽取到关系: {len(relations)} 个")

        # 6. 知识存储 (加载到 Neo4j)
        print("\n[阶段4: 知识存储]")
        data_loader.load_entities(db_conn, entities)
        print(f"成功加载 {len(entities)} 个实体节点。")
        data_loader.load_relations(db_conn, relations)
        print(f"成功加载 {len(relations)} 个关系。")

        print("\n--- 知识图谱构建流程完毕 ---")

    except Exception as e:
        print(f"\n流程发生严重错误: {e}")
    finally:
        db_conn.close()
        print("数据库连接已关闭。")


if __name__ == "__main__":
    main_pipeline()