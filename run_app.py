# 启动智能应用（如问答Web服务）的主脚本
from flask import Flask, request, jsonify
import configparser
from kg_course_project.graph_db.connection import Neo4jConnection
from kg_course_project.applications import qa_system

# --- 全局初始化 ---
app = Flask(__name__)

# 加载配置
config = configparser.ConfigParser()
config.read('config.ini')
neo4j_uri = config['NEO4J']['URI']
neo4j_auth = (config['NEO4J']['USER'], config['NEO4J']['PASSWORD'])

# 创建全局数据库连接
# 注意：在生产环境中，更推荐使用连接池或在每个请求中管理会话
# 但为简化MVP，我们创建一个长连接。
try:
    db_conn = Neo4jConnection(uri=neo4j_uri, auth=neo4j_auth)
    db_conn.driver.verify_connectivity()
    print(f"成功连接到 Neo4j 数据库: {neo4j_uri}")
except Exception as e:
    print(f"无法连接到 Neo4j，请检查 config.ini 和数据库状态: {e}")
    db_conn = None


# --- API 路由定义 ---

@app.route('/')
def index():
    return "知识图谱问答系统 API 已启动。请使用 /ask"


@app.route('/ask', methods=['GET'])
def ask_question():
    if not db_conn:
        return jsonify({"error": "数据库未连接"}), 500

    question = request.args.get('q')
    if not question:
        return jsonify({"error": "缺少参数 'q' (问题)"}), 400

    # (MVP) 简化NLU，我们假设问题就是实体名称
    # 真实项目：这里需要 NLU 来解析意图和实体
    entity_name = question.strip()

    # (MVP) 简化意图识别，我们只实现一种查询："查询前置知识"
    # 真实项目：根据NLU的意图调用不同的 qa_system 函数

    try:
        prereqs = qa_system.find_prerequisites(db_conn, entity_name)

        if not prereqs:
            answer = f"未找到 '{entity_name}' 的前置知识，或该概念不存在。"
        else:
            answer = f"学习 '{entity_name}' 的前置知识包括: {', '.join(prereqs)}"

        return jsonify({
            "question": question,
            "entity_detected": entity_name,
            "answer": answer,
            "data": prereqs
        })

    except Exception as e:
        return jsonify({"error": f"查询时发生错误: {e}"}), 500


if __name__ == '__main__':
    print("启动 Flask Web 服务器在 http://127.0.0.1:5000 ...")
    app.run(debug=True, port=5000)