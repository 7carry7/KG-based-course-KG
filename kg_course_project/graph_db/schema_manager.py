# 创建约束和索引 (对应阶段1)
from kg_course_project.utils.file_io import read_yaml
import time
from kg_course_project.utils.logger import get_logger
from neo4j.exceptions import ClientError

logger = get_logger(__name__)

def clear_database(conn, confirm=False):

    if not confirm:
        raise ValueError('此操作会清空所有数据！请设置 confirm=True 来确认')

    """
        清空所有节点和关系 (危险操作)。
        使用 DETACH DELETE 以删除节点及其所有关系。
        """
    logger.warning("正在清空整个数据库 (所有节点和关系)...")
    try:
        conn.run_query("MATCH (n) DETACH DELETE n")
        logger.info("数据库已清空。")
    except Exception as e:
        logger.error(f"清空数据库时出错: {e}")


def drop_all_schema(conn):
    """
    删除数据库中所有的索引和约束。
    用于测试环境的完全重置。
    """
    logger.info("正在删除所有索引和约束...")

    # 1. 获取所有约束
    constraints = conn.run_query("SHOW CONSTRAINTS")
    for record in constraints:
        name = record["name"]
        logger.info(f"正在删除约束: {name}")
        try:
            conn.run_query(f"DROP CONSTRAINT {name}")
        except ClientError as e:
            logger.warning(f"删除约束 {name} 失败 (可能已不存在): {e}")

    # 2. 获取所有索引 (注意: 约束自动创建的索引也会在这里，但DROP CONSTRAINT会处理它们)
    indexes = conn.run_query("SHOW INDEXES")
    for record in indexes:
        name = record["name"]
        # 约束创建的索引不能用 DROP INDEX 删除, 会报错
        if "constraint" not in record["type"].lower():
            logger.info(f"正在删除索引: {name}")
            try:
                conn.run_query(f"DROP INDEX {name}")
            except ClientError as e:
                logger.warning(f"删除索引 {name} 失败 (可能已不存在): {e}")

    logger.info("所有索引和约束已删除。")


def apply_schema_from_yaml(conn, schema_path):
    """
    (丰富版) 根据 schema.yaml 文件应用所有约束和索引。
    支持: 'unique' 约束, 'simple' 索引 (B-Tree), 'fulltext' 索引。
    """
    schema = read_yaml(schema_path)

    # --- 1. 应用节点模式 ---
    logger.info("开始应用节点 (Node) 模式...")
    # schema is a dict
    for node in schema.get('nodes', []):
        label = node['label']
        for prop in node.get('properties', []):
            prop_name = prop['name']

            # 1a. 唯一性约束 (Unique Constraint)
            if prop.get('constraint') == 'unique':
                query = f"""
                CREATE CONSTRAINT IF NOT EXISTS FOR (n:{label}) 
                REQUIRE n.{prop_name} IS UNIQUE
                """
                conn.run_query(query)
                logger.info(f"已应用 [Unique Constraint] ON (:{label}) [{prop_name}]")

            # 1b. 简单索引 (B-Tree Index)
            elif prop.get('index') == 'simple':
                index_name = f"idx_{label}_{prop_name}"
                query = f"""
                CREATE INDEX {index_name} IF NOT EXISTS FOR (n:{label}) 
                ON (n.{prop_name})
                """
                conn.run_query(query)
                logger.info(f"已应用 [Simple Index] ON (:{label}) [{prop_name}]")

            # 1c. 全文索引 (Full-Text Index)
            elif prop.get('index') == 'fulltext':
                index_name = f"ft_idx_{label}_{prop_name}"

                query = f"""
                CREATE FULLTEXT INDEX {index_name} IF NOT EXISTS FOR (n:{label}) 
                ON EACH [n.{prop_name}]
                """
                try:
                    conn.run_query(query)
                    logger.info(f"已应用 [Fulltext Index] ON (:{label}) [{prop_name}]")
                except ClientError as e:
                    logger.warning(f"无法创建全文索引 '{index_name}' (可能已存在或配置不支持): {e}")

    # # --- 2. 应用关系模式 ---
    # logger.info("开始应用关系 (Relationship) 模式...")
    # for rel in schema.get('relationships', []):
    #     rel_type = rel['type']
    #     for prop in rel.get('properties', []):
    #         prop_name = prop['name']
    #
    #         # 2a. 关系属性索引 (B-Tree Index)
    #         if prop.get('index') == 'simple':
    #             index_name = f"idx_rel_{rel_type}_{prop_name}"
    #             query = f"""
    #             CREATE INDEX {index_name} IF NOT EXISTS FOR ()-[r:{rel_type}]-()
    #             ON (r.{prop_name})
    #             """
    #             conn.run_query(query)
    #             logger.info(f"已应用 [Rel Index] ON (:{rel_type}) [{prop_name}]")

    logger.info("模式应用完毕。")


def await_indexes_online(conn, timeout_seconds=300):
    """
    (关键) 轮询数据库，等待所有索引和约束都处于 'ONLINE' 状态。
    这是在写入大量数据之前必须执行的步骤。
    """
    logger.info("正在等待所有索引和约束变为 'ONLINE'...")
    start_time = time.time()

    while time.time() - start_time < timeout_seconds:
        try:
            # GDS 1.x 使用 'db.indexes()', Neo4j 4.x+ 使用 'SHOW INDEXES'
            # 'SHOW ...' 是更标准的方式
            indexes = conn.run_query("SHOW INDEXES")
            constraints = conn.run_query("SHOW CONSTRAINTS")

            all_online = True

            # 检查索引
            for record in indexes:
                state = record.get("state", "ONLINE").upper()  # 默认为 ONLINE
                if state != "ONLINE":
                    all_online = False
                    logger.info(f"索引 '{record['name']}' 状态为: {state} (正在等待...)")

            # 检查约束 (约束通常很快，但最好也检查)
            for record in constraints:
                state = record.get("state", "ONLINE").upper()
                if state != "ONLINE":
                    all_online = False
                    logger.info(f"约束 '{record['name']}' 状态为: {state} (正在等待...)")

            if all_online:
                logger.info("所有索引和约束均已 'ONLINE'。")
                return True

        except Exception as e:
            logger.warning(f"检查索引状态时出错: {e}")

        time.sleep(3)  # 轮询间隔

    logger.error(f"索引在 {timeout_seconds} 秒内未能变为 'ONLINE'。流程终止。")
    raise TimeoutError(f"索引未能在 {timeout_seconds} 秒内上线")


def show_schema(conn):
    """
    (工具函数) 打印数据库中当前所有的约束和索引。
    """
    print("\n--- 数据库模式概览 ---")

    try:
        print("\n[约束 (Constraints)]")
        constraints = conn.run_query("SHOW CONSTRAINTS")
        if not constraints:
            print("  (无)")
        for record in constraints:
            print(
                f"  - 名称: {record['name']}\n    类型: {record['type']}\n    详情: {record['labelsOrTypes']}[{record['properties']}]")

        print("\n[索引 (Indexes)]")
        indexes = conn.run_query("SHOW INDEXES")
        if not indexes:
            print("  (无)")
        for record in indexes:
            # 过滤掉由约束自动创建的索引，避免重复显示
            if "constraint" not in record["type"].lower():
                print(
                    f"  - 名称: {record['name']}\n    类型: {record['type']} ({record.get('provider', 'N/A')})\n    状态: {record['state']}\n    详情: {record['labelsOrTypes']}[{record['properties']}]")

    except Exception as e:
        logger.error(f"无法显示模式: {e}")

    print("-------------------------")


if __name__ == "__main__":
    # --- 测试 ---
    import configparser
    from kg_course_project.graph_db.connection import Neo4jConnection

    config = configparser.ConfigParser()
    try:
        config.read('../../config.ini', encoding='utf-8')
        uri = config['NEO4J']['URI']
        auth = (config['NEO4J']['USER'], config['NEO4J']['PASSWORD'])
    except KeyError:
        print("错误: 无法读取 config.ini 或配置不完整。")
        print("请确保 config.ini 存在于根目录并包含 [NEO4J] 部分。")
        exit(1)

    schema_file = '../../schema.yaml'

    conn = None
    try:
        conn = Neo4jConnection(uri=uri, auth=auth)
        conn.driver.verify_connectivity()
        logger.info("数据库连接成功。")

        # 1. (危险) 重置环境
        logger.info("--- 步骤 1: 重置数据库 ---")
        clear_database(conn, confirm=True)
        drop_all_schema(conn)

        # 2. 应用新模式
        logger.info("\n--- 步骤 2: 应用新模式 ---")
        apply_schema_from_yaml(conn, schema_file)

        # 3. 等待索引上线
        logger.info("\n--- 步骤 3: 等待索引上线 ---")
        await_indexes_online(conn, timeout_seconds=60)

        # 4. 显示结果
        logger.info("\n--- 步骤 4: 显示最终模式 ---")
        show_schema(conn)

    except Exception as e:
        logger.error(f"主测试流程失败: {e}")
    finally:
        if conn:
            conn.close()
            logger.info("数据库连接已关闭。")