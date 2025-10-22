# 实体识别 (spaCy, BERT)
import spacy
from spacy.pipeline import EntityRuler
from kg_course_project.utils.logger import get_logger
import os

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
    if nlp is None:
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
    if nlp is None:
        return []

    # 确保 EntityRuler 只被添加一次
    if "entity_ruler" not in nlp.pipe_names:
        create_domain_entity_ruler(domain_vocab)

    doc = nlp(text)

    entities = []
    for ent in doc.ents:
        entities.append({
            "name": ent.text,
            "label": ent.label_,
            "start_char": ent.start_char,
            "end_char": ent.end_char
        })

    return entities


if __name__ == "__main__":
    test_text = "在知识图谱课程中, 我们学习 RDF 和 RDFS。 spaCy 是一个强大的工具, 由 Google 的张三开发。"

    test_vocab = {
        "Concept": ["RDF", "RDFS", "知识图谱"],
        "Technology": ["spaCy"],
    }

    print("--- (新) 混合实体抽取测试 ---")

    # 第一次运行会加载模型并添加Ruler
    entities_hybrid = extract_entities_hybrid(test_text, test_vocab)
    # print(entities_hybrid)

    for entity in entities_hybrid:
        print(entity)

    # 预期结果会包含:
    # {'name': '知识图谱', 'label': 'Concept', ...}  (来自Ruler)
    # {'name': 'RDF', 'label': 'Concept', ...}      (来自Ruler)
    # {'name': 'RDFS', 'label': 'Concept', ...}     (来自Ruler)
    # {'name': 'spaCy', 'label': 'Technology', ...} (来自Ruler, 覆盖了可能的ORG)
    # {'name': 'Google', 'label': 'ORG', ...}      (来自spaCy预训练模型)
    # {'name': '张三', 'label': 'PERSON', ...}    (来自spaCy预训练模型)