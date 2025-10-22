# 关系抽取 (规则, 模型)
import re
from spacy.tokens import Doc
from kg_course_project.extraction.ner import NLP, load_spacy_model
from kg_course_project.utils.logger import get_logger

logger = get_logger(__name__)


# --- (方法1：基于高精度正则表达式) ---
def extract_relations_by_rules(text, entities, rules):
    """
    (MVP) 基于正则表达式规则的关系抽取。
    :param text: 清洗后的文本
    :param entities: NER 抽取到的实体列表
    :param rules: 规则列表 (regex, type, head_group_idx, tail_group_idx)
    :return: 关系三元组列表 [{"head": "OWL", "head_label": "Concept", "type": "REQUIRES_PRE", "tail": "RDFS", "tail_label": "Concept"}]
    """
    relations = []

    # 为了快速查找实体的标签
    entity_map = {e['name']: e['label'] for e in entities}

    sentences = re.split(r'[。？！；]', text)  # 简单按句号分句

    for sentence in sentences:
        for rule_pattern, rel_type, head_idx, tail_idx in rules:
            matches = re.finditer(rule_pattern, sentence)

            for match in matches:
                try:
                    head_name = match.group(head_idx).strip()
                    tail_names_raw = match.group(tail_idx).strip()

                    # 特殊处理 "INCLUDES_CONCEPT" (一对多)
                    if rel_type == 'INCLUDES_CONCEPT':
                        tail_names = [name.strip() for name in tail_names_raw.split('，')]  # 按中文逗号分割
                    else:
                        tail_names = [tail_names_raw]

                    for tail_name in tail_names:
                        # 检查抽到的头尾实体是否在我们已识别的实体列表中
                        if head_name in entity_map and tail_name in entity_map:
                            relations.append({
                                "head": head_name,
                                "head_label": entity_map[head_name],
                                "type": rel_type,
                                "tail": tail_name,
                                "tail_label": entity_map[tail_name]
                            })
                except IndexError:
                    pass  # 正则匹配组失败

    return relations


# --- (方法2：基于 spaCy 句法依赖) ---
# 这是一个简化的示例，查找 "EntityA [动词] EntityB" 模式
def extract_relations_spacy(doc: Doc, entities: list, domain_vocab: dict):
    """
    (新) 基于 spaCy 依赖和共现的关系抽取。

    :param doc: 经过 ner.py 处理的 spaCy Doc 对象
    :param entities: ner.py 抽取的实体列表
    :param domain_vocab: 领域词典, 用于判断实体类型
    :return: 关系三元组列表
    """
    relations = []

    # 构建一个从 start_char 到实体信息的快速查找字典
    ent_lookup = {e['start_char']: e for e in entities}

    for sent in doc.sents:
        sent_ents = [ent for ent in sent.ents if ent.start_char in ent_lookup]

        # 如果一个句子中少于2个实体, 不太可能有关系
        if len(sent_ents) < 2:
            print('continue')
            continue

        # 遍历句子中所有实体对
        for i in range(len(sent_ents)):
            for j in range(i + 1, len(sent_ents)):
                ent_head = sent_ents[i]
                ent_tail = sent_ents[j]

                # 在两个实体之间的文本
                inter_text = doc.char_span(ent_head.end_char, ent_tail.start_char)
                if inter_text is None:
                    continue

                inter_text_str = inter_text.text.strip()
                print(inter_text_str)

                # --- 在此定义句法规则 ---

                # 规则1: "A 是 B" -> IS_A 关系 (简化)
                if inter_text_str == "是":
                    relations.append(build_relation(ent_lookup[ent_head.start_char],
                                                    "IS_A",
                                                    ent_lookup[ent_tail.start_char]))

                # 规则2: "A 包含 B" -> INCLUDES 关系
                if "包含" in inter_text_str or "包括" in inter_text_str:
                    relations.append(build_relation(ent_lookup[ent_head.start_char],
                                                    "INCLUDES_CONCEPT",  # 假设
                                                    ent_lookup[ent_tail.start_char]))

                # 规则3: "A 由 B 开发" -> DEVELOPED_BY 关系
                if "由" in inter_text_str and "开发" in inter_text_str:
                    relations.append(build_relation(ent_lookup[ent_head.start_char],
                                                    "DEVELOPED_BY",
                                                    ent_lookup[ent_tail.start_char]))

    return relations


def build_relation(head, rel_type, tail):
    """辅助函数：构建关系字典"""
    return {
        "head": head['name'],
        "head_label": head['label'],
        "type": rel_type,
        "tail": tail['name'],
        "tail_label": tail['label']
    }


if __name__ == "__main__":
    # --- 测试 ---
    test_text = ("知识图谱包含RDF 。spaCy 是由 Google 开发。")
    test_vocab = {
        "Concept": ["RDF", "知识图谱"],
        "Technology": ["spaCy"],
        "ORG": ["Google"]  # spaCy 也能识别
    }

    # 1. 运行 NER (这会加载模型)
    from kg_course_project.extraction.ner import extract_entities_hybrid

    entities = extract_entities_hybrid(test_text, test_vocab)
    print(f"--- 抽取到的实体: ---\n{entities}\n")

    # 2. 运行 RE
    nlp = load_spacy_model()
    doc = nlp(test_text)

    relations = extract_relations_spacy(doc, entities, test_vocab)
    print(f"--- 抽取到的关系 (spaCy): ---\n{relations}\n")

    # 预期:
    # {'head': '知识图谱', 'head_label': 'Concept', 'type': 'INCLUDES_CONCEPT', 'tail': 'RDF', 'tail_label': 'Concept'}
    # {'head': 'spaCy', 'head_label': 'Technology', 'type': 'DEVELOPED_BY', 'tail': 'Google', 'tail_label': 'ORG'}