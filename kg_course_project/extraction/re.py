# 关系抽取 (规则, 模型)
import re


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