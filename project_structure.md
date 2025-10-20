knowledge_graph_course/
├── .gitignore
├── README.md
├── requirements.txt
├── config.ini                # 数据库连接, API密钥, 模型路径 (敏感信息)
├── schema.yaml               # 阶段1：本体层的 YAML 描述 (清晰易读)
├── run_pipeline.py           # 运行整个数据处理和图谱构建流程的主脚本
├── run_app.py                # 启动智能应用（如问答Web服务）的主脚本
│
├── kg_course_project/        # 核心 Python 源代码包
│   ├── __init__.py
│   │
│   ├── data_acquisition/     # 阶段2.1：数据爬取和解析
│   │   ├── __init__.py
│   │   ├── scrape_web.py       # 爬取课程网页
│   │   ├── parse_pdf.py        # 解析教材PDF
│   │   └── data_cleaner.py     # 文本清洗
│   │
│   ├── extraction/           # 阶段2.2 & 3：知识抽取与融合
│   │   ├── __init__.py
│   │   ├── ner.py              # 实体识别 (spaCy, BERT)
│   │   ├── re.py               # 关系抽取 (规则, 模型)
│   │   └── fusion.py           # 知识融合/实体对齐
│   │
│   ├── graph_db/             # 阶段4：知识存储 (Neo4j)
│   │   ├── __init__.py
│   │   ├── connection.py       # Neo4j 驱动连接管理
│   │   ├── schema_manager.py   # 创建约束和索引 (对应阶段1)
│   │   └── data_loader.py      # 将抽取的实体和关系写入数据库
│   │
│   ├── applications/         # 阶段5：智能应用
│   │   ├── __init__.py
│   │   ├── search.py           # 智能搜索 (Cypher 查询封装)
│   │   ├── qa_system.py        # 智能问答 (NLU + Cypher)
│   │   ├── inference.py        # 知识推理 (如路径推理)
│   │   └── recommender.py      # 学习路径推荐 (图算法)
│   │
│   └── utils/                # 通用工具
│       ├── __init__.py
│       ├── logger.py           # 日志配置
│       └── file_io.py          # 文件读写帮助函数
│
├── data/                     # 数据文件 (不提交到 Git)
│   ├── raw/                  # 原始数据
│   │   ├── syllabus.pdf
│   │   └── chapter1.html
│   ├── processed/            # 清洗和处理后的中间数据
│   │   ├── cleaned_text.txt
│   │   └── extracted_triples.json
│   └── output/               # 最终输出（如果需要）
│       └── kg_export.json
│
├── models/                   # 训练好的模型或词典 (不提交到 Git)
│   ├── ner_model/            # 自定义NER模型
│   └── vocab.txt             # 领域词典
│
├── notebooks/                # Jupyter Notebooks (用于探索和调试)
│   ├── 01_data_exploration.ipynb # 数据探索
│   ├── 02_model_training.ipynb   # 抽取模型训练
│   └── 03_graph_queries.ipynb    # 图查询和可视化测试
│
└── tests/                    # 单元测试和集成测试
    ├── __init__.py
    ├── test_extraction.py
    ├── test_graph_db.py
    └── test_applications.py