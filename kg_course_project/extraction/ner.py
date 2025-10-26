# 实体识别 (spaCy, BERT)
import spacy
from spacy.pipeline import EntityRuler
from kg_course_project.utils.logger import get_logger
import fusion
from kg_course_project.data_acquisition import scrape_web
from functools import lru_cache
from spacy.util import filter_spans
import sys

logger = get_logger(__name__)

# --- 全局 NLP 模型加载 ---
# 避免在每次调用函数时都重新加载模型
NLP = None


def load_spacy_model(model_name="zh_core_web_md"):
    """加载 spaCy 模型并配置 EntityRuler"""
    global NLP
    if NLP is None:
        try:
            NLP = spacy.load(model_name)
            logger.info(f"成功加载 spaCy 模型: {model_name}")
        except OSError:
            logger.error(f"无法加载 spaCy 模型 '{model_name}'。")
            logger.error(f"请运行: python -m spacy download {model_name}")
            return None
    return NLP


def create_domain_entity_ruler(vocab):
    """
    根据我们的领域词典创建 spaCy EntityRuler 规则。
    :param vocab: 字典, 格式 { "Label1": ["entity1", "entity2"], ... }
    :return: EntityRuler 实例
    """
    nlp = load_spacy_model()
    # nlp = NLP
    if nlp is None:
        # nlp = load_spacy_model()
        raise ValueError("spaCy 模型未加载")

    ruler = nlp.add_pipe("entity_ruler", before="ner")

    patterns = []
    for label, names in vocab.items():
        for name in names:
            patterns.append({"label": label, "pattern": name})

    ruler.add_patterns(patterns)
    logger.info(f"EntityRuler 已配置 {len(patterns)} 条领域词典规则。")
    return ruler


# --- 旧的基于词典的方法 (保留对比) ---
def extract_entities_by_vocab(text, vocab):
    """
    (MVP) 基于词典的实体抽取。
    :param text: 清洗后的文本
    :param vocab: 字典, 格式 { "Label1": ["entity1", "entity2"], ... }
    :return: 实体列表, 格式 [{"name": "RDF", "label": "Concept"}]
    """
    entities_found = []
    found_names = set()  # 避免重复添加

    for label, names in vocab.items():
        for name in names:
            # 确保我们匹配的是完整的词 (虽然中文不明显，但对英文有好处)
            # 简单的查找
            if name in text and name not in found_names:
                entities_found.append({"name": name, "label": label})
                found_names.add(name)

    return entities_found


# --- 新的混合方法 ---
def extract_entities_hybrid(text, domain_vocab):
    """
    (新) 混合实体抽取：
    1. 优先使用领域词典 (通过 EntityRuler)。
    2. 其次使用 spaCy 的预训练模型 (如 PER, ORG, LOC)。

    :param text: 清洗后的文本
    :param domain_vocab: 我们的领域词典
    :return: 实体列表, 格式 [{"name": "RDF", "label": "Concept", "start_char": 10, "end_char": 13}]
    """
    nlp = load_spacy_model()
    # nlp = NLP
    if nlp is None:
        # nlp = load_spacy_model()
        return []

    # 确保 EntityRuler 只被添加一次
    if "entity_ruler" not in nlp.pipe_names:
        create_domain_entity_ruler(domain_vocab)

    doc = nlp(text)

    entities = []
    for ent in filter_spans(doc.ents):
        entities.append({
            "name": ent.text,
            "label": ent.label_,
            "start_char": ent.start_char,
            "end_char": ent.end_char
        })

    return entities


def scrape(uri):
    url = uri.rstrip("/")

    print(f"--- 正在测试爬取: {url} ---")
    web_text = scrape_web.fetch_webpage_text(url)

    if web_text:
        print(f"成功获取文本: \n{web_text[:]}...")

        # 测试与清理器集成
        from kg_course_project.data_acquisition.data_cleaner import clean_text_pipeline

        print("\n--- 清理后的文本 ---")
        cleaned_text = clean_text_pipeline(web_text)
        # print(cleaned_text[:] + "...")
        print("clean successfully!")
        return cleaned_text
    else:
        print("爬取失败。")
        return None

if __name__ == "__main__":
    # load_spacy_model()
    # test_text = "在知识图谱课程中, 我们学习 RDF 和 RDFS。 spaCy 是一个强大的工具, 由 Google 的张三开发。"
    #
    # test_vocab = {
    #     "Concept": ["RDF", "RDFS", "知识图谱"],
    #     "Technology": ["spaCy"],
    # }

    domain_vocab = {
        # --- 课程章节（Chapter） ---
        "Chapter": [
            "知识图谱概述", "知识图谱基础", "知识表示", "知识获取与抽取",
            "知识融合", "知识推理", "知识存储与查询", "知识图谱应用",
            "开放知识图谱", "领域知识图谱", "知识图谱评估"
        ],

        # --- 核心算法（Algorithm） ---
        "Algorithm": [
            "TransE", "TransH", "TransR", "TransD", "ComplEx", "DistMult", "RotatE",
            "GraphSAGE", "GCN", "GAT", "R-GCN", "BERT", "ERNIE", "CoKE",
            "OpenIE", "REBEL", "GPT", "DeepWalk", "Node2Vec", "LINE"
        ],

        # --- 技术框架（Technology / Framework） ---
        "Technology": [
            "Neo4j", "RDF", "SPARQL", "OWL", "RDFS", "Protégé",
            "Jena", "GraphDB", "Stardog", "ArangoDB", "OrientDB",
            "NetworkX", "DGL", "PyTorch Geometric", "TensorFlow", "Hugging Face"
        ],

        # --- 核心概念（Concept） ---
        "Concept": [
            "知识表示", "知识抽取", "实体识别", "关系抽取", "属性抽取", "知识融合",
            "本体建模", "语义相似度", "三元组", "实体消歧", "上下位关系",
            "知识推理", "知识补全", "推理规则", "知识存储", "知识检索",
            "本体", "实体", "关系", "属性", "RDF三元组", "语义网络",
            "本体层", "实例层", "知识层", "概念层", "语义层"
        ],

        # --- 应用场景（Application） ---
        "Application": [
            "智能问答", "语义搜索", "推荐系统", "对话系统", "智能客服",
            "医学", "教育", "金融知识图谱", "法律", "电子商务",
            "企业", "公共安全", "科研", "医疗保健", "生物制药",
            "知识可视化", "语义检索", "因果推理", "情感分析", "财务金融"
        ],

        # --- 数据来源与标准（DataSource / Standard） ---
        "DataSource": [
            "DBpedia", "YAGO", "Freebase", "Wikidata", "CN-DBpedia", "OpenKG",
            "WordNet", "ConceptNet", "BaiduBaike", "Zhishi.me"
        ],

        # # --- 工具与库（Tool） ---
        # "Tool": [
        #     "Neo4j Browser", "Cypher", "Protégé", "GraphDB", "Jena",
        #     "SPARQL Endpoint", "RDFLib", "NetworkX", "Pandas", "Matplotlib"
        # ],

        # --- 方法论与框架（Methodology / Framework） ---
        # "Framework": [
        #     "语义网框架", "RDF框架", "本体驱动建模", "端到端知识图谱构建",
        #     "基于规则的推理", "基于嵌入的推理", "混合推理框架", "本体学习"
        # ],

        # # --- 任务（Task） ---
        # "Task": [
        #     "实体抽取", "关系抽取", "属性抽取", "本体对齐",
        #     "实体链接", "关系预测", "知识补全", "知识融合",
        #     "知识推理", "知识可视化", "知识检索"
        # ],

        # --- 指标（Metric） ---
        "Metric": [
            "精确率", "召回率", "F1值", "Hit@10", "MRR", "MAP",
            "AUC", "覆盖率", "一致性", "可扩展性"
        ]
    }

    # print("--- (新) 混合实体抽取测试 ---")
    #
    # # 第一次运行会加载模型并添加Ruler
    # entities_hybrid = extract_entities_hybrid(test_text, test_vocab)
    # # print(entities_hybrid)
    #
    # for entity in entities_hybrid:
    #     print(entity)

    # 预期结果会包含:
    # {'name': '知识图谱', 'label': 'Concept', ...}  (来自Ruler)
    # {'name': 'RDF', 'label': 'Concept', ...}      (来自Ruler)
    # {'name': 'RDFS', 'label': 'Concept', ...}     (来自Ruler)
    # {'name': 'spaCy', 'label': 'Technology', ...} (来自Ruler, 覆盖了可能的ORG)
    # {'name': 'Google', 'label': 'ORG', ...}      (来自spaCy预训练模型)
    # {'name': '张三', 'label': 'PERSON', ...}    (来自spaCy预训练模型)

    # wiki_url = "https://zh.wikipedia.org/wiki/知识图谱"
    wiki_url = "https://blog.itpub.net/69925873/viewspace-3086672/"
    text = scrape(wiki_url)
    if text is None:
        sys.exit("scrape failure")
    else:

        print("--- (新) 混合实体抽取测试 ---")

        # 第一次运行会加载模型并添加Ruler
        entities_hybrid = extract_entities_hybrid(text, domain_vocab)
        # print(entities_hybrid)
        entities_hybrid = fusion.filter_entities(entities_hybrid)

        print("--- 1. 创建规范化 Map ---")
        cmap = fusion.create_canonical_map(entities_hybrid, similarity_threshold=0.8)
        print(f"Map: {cmap}")

        print("--- 2. 实体清晰 ---")
        entities_hybrid = fusion.resolve_entities(entities_hybrid, canonical_map=cmap)

        for entity in entities_hybrid:
            print(entity)
