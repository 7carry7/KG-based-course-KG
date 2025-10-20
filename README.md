# 《知识图谱》课程知识图谱 (MVP)

这是一个基于Python和Neo4j的《知识图谱》课程知识图谱的最小可行项目 (MVP)。

## 项目结构

项目遵循专业的数据工程和AI项目结构，将数据、源码、配置和应用分离。

## 安装与设置

1.  **安装 Neo4j**:
    * 确保 Neo4j 数据库正在运行（通常在 `bolt://localhost:7687`）。

2.  **安装 Python 依赖**:
    ```bash
    pip install -r requirements.txt
    ```

3.  **配置数据库**:
    * 复制 `config.ini.template` (见下方) 为 `config.ini`。
    * 在 `config.ini` 中填入你的 Neo4j 用户名和密码。

4.  **创建模拟数据 (关键步骤)**:
    * 在 `data/raw/` 目录下创建一个名为 `course_content.txt` 的文件。
    * 将以下模拟课程内容复制到该文件中：
    
    ```text
    知识图谱课程大纲。
    第一章：知识表示。本章包含的概念有：RDF，RDFS，OWL。
    RDF 是 RDFS 的基础。OWL 需要 RDFS。
    第二章：知识抽取。本章包含的概念有：实体识别，关系抽取。
    实体识别使用 spaCy 技术。关系抽取使用 BERT 算法。
    第三章：知识存储。本章使用 Neo4j 技术。
    ```

## 如何运行

1.  **运行数据处理管道 (ETL)**:
    * 这将清空数据库，创建模式，读取 `data/raw/course_content.txt`，抽取实体和关系，并存入 Neo4j。
    ```bash
    python run_pipeline.py
    ```

2.  **运行智能问答 Web 应用**:
    ```bash
    python run_app.py
    ```

3.  **测试应用**:
    * 打开一个新的终端，使用 `curl` 测试：
    ```bash
    # 测试：学习 "OWL" 需要什么前置知识？
    curl "[http://127.0.0.1:5000/ask?q=OWL](http://127.0.0.1:5000/ask?q=OWL)"
    ```