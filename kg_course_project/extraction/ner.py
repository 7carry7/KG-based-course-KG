# 实体识别 (spaCy, BERT)
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