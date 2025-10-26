# 知识融合/实体对齐
import Levenshtein
from collections import defaultdict
from kg_course_project.utils.logger import get_logger
import re
from collections import Counter

logger = get_logger(__name__)


def normalize_entity_name(name):
    """
    标准化实体名称，以便于比较。
    - 转为小写
    - 去除首尾空格
    - 去除所有标点符号和空格
    """
    name = name.lower().strip()
    name = re.sub(r"[\s\.\-,_]", "", name)
    return name


def create_canonical_map(entities, similarity_threshold=0.85):
    """
    对抽取的实体列表进行聚类, 生成一个“别名 -> 规范名”的映射。

    例如: {"bert": "bert", "bidirectionalencoder...": "bert"}

    :param entities: ner.py 抽取的实体列表 (e.g., [{"name": "BERT", "label": "Algorithm"}])
    :param similarity_threshold: Levenshtein 相似度阈值
    :return: 规范化映射 (dict)
    """

    # 按标签分组，我们只对同一类型的实体进行融合
    grouped_by_label = defaultdict(list)
    for ent in entities:
        # 我们只关心我们定义的核心实体
        if ent['label'] in ["Concept", "Technology", "Algorithm", "Scholar", "Chapter"
                            "Course", "Paper", "Application", "Metric"]:
            grouped_by_label[ent['label']].append(ent['name'])

    canonical_map = {}

    for label, names in grouped_by_label.items():
        unique_names = sorted(list(set(names)), key=len)  # 从短的开始，倾向于用短的做规范名
        clusters = []  # 存放规范名 (每个簇的代表)

        for name in unique_names:
            norm_name = normalize_entity_name(name)
            if norm_name in canonical_map:  # 已经被处理过
                continue

            found_cluster = False
            for canonical_name in clusters:
                norm_canonical = normalize_entity_name(canonical_name)

                # 计算相似度
                ratio = Levenshtein.ratio(norm_name, norm_canonical)

                if ratio >= similarity_threshold:
                    logger.info(f"[Fusion] 实体对齐: '{name}' -> '{canonical_name}' (相似度: {ratio:.2f})")
                    canonical_map[norm_name] = canonical_name
                    found_cluster = True
                    break

            if not found_cluster:
                # 这是一个新的簇，它自己就是规范名
                clusters.append(name)
                canonical_map[norm_name] = name

    logger.info(f"实体融合完成, 生成 {len(canonical_map)} 条规范化规则。")
    return canonical_map

def resolve_entities(entities, canonical_map):
    resolved_entities = []
    seen_entities = set()

    # 1. 解析实体列表
    for ent in entities:
        norm_name = normalize_entity_name(ent['name'])

        # 检查是否需要被融合
        if norm_name in canonical_map:
            canonical_name = canonical_map[norm_name]

            # 只添加规范化后的实体，并确保去重
            if (canonical_name, ent['label']) not in seen_entities:
                resolved_entities.append({"name": canonical_name, "label": ent['label']})
                seen_entities.add((canonical_name, ent['label']))
        else:
            # 这个实体不在我们的融合范围内 (例如 PER, LOC)，直接添加
            if (ent['name'], ent['label']) not in seen_entities:
                resolved_entities.append(ent)
                seen_entities.add((ent['name'], ent['label']))

    return resolved_entities

def resolve_relations(relations, canonical_map):
    """
    使用 canonical_map 来清洗实体列表和关系列表。

    :param entities: 原始实体列表
    :param relations: 原始关系列表
    :param canonical_map: create_canonical_map() 的输出
    :return: (resolved_entities, resolved_relations)
    """

    # resolved_entities = []
    # seen_entities = set()
    #
    # # 1. 解析实体列表
    # for ent in entities:
    #     norm_name = normalize_entity_name(ent['name'])
    #
    #     # 检查是否需要被融合
    #     if norm_name in canonical_map:
    #         canonical_name = canonical_map[norm_name]
    #
    #         # 只添加规范化后的实体，并确保去重
    #         if (canonical_name, ent['label']) not in seen_entities:
    #             resolved_entities.append({"name": canonical_name, "label": ent['label']})
    #             seen_entities.add((canonical_name, ent['label']))
    #     else:
    #         # 这个实体不在我们的融合范围内 (例如 PER, LOC)，直接添加
    #         if (ent['name'], ent['label']) not in seen_entities:
    #             resolved_entities.append(ent)
    #             seen_entities.add((ent['name'], ent['label']))

    # 2. 解析关系列表
    resolved_relations = []
    seen_relations = set()

    for rel in relations:
        norm_head = normalize_entity_name(rel['head'])
        norm_tail = normalize_entity_name(rel['tail'])

        # 查找头尾实体的规范名
        resolved_head = canonical_map.get(norm_head, rel['head'])
        resolved_tail = canonical_map.get(norm_tail, rel['tail'])

        rel_key = (resolved_head, rel['type'], resolved_tail)

        # 关系去重
        if rel_key not in seen_relations:
            resolved_relations.append({
                "head": resolved_head,
                "head_label": rel['head_label'],
                "type": rel['type'],
                "tail": resolved_tail,
                "tail_label": rel['tail_label']
            })
            seen_relations.add(rel_key)

    return resolved_relations

# 常见无意义词
STOP_WORDS = {"的", "和", "或", "方法", "系统", "任务", "模型"}


def filter_entities(entities, min_len=2, min_freq=2):
    """
    对抽取的实体执行过滤逻辑。
    :param entities: [{'name': ..., 'label': ..., ...}, ...]
    :return: 过滤后的实体列表
    """
    # 统计频次
    freq = Counter(ent["name"] for ent in entities)
    filtered = []

    for ent in entities:
        name = ent["name"].strip()
        label = ent["label"]

        # 1. 长度过滤
        if len(name) < min_len:
            continue

        # 2. 停用词过滤
        if name in STOP_WORDS:
            continue

        # 3. 频次过滤
        if freq[name] < min_freq:
            continue

        # 4. 合法字符检查
        if not re.match(r'^[\u4e00-\u9fa5a-zA-Z0-9_+\-]+$', name):
            continue

        # 5. 限定标签（只保留关键类别）
        if label not in {"Concept", "Algorithm", "Technology", "Application", "Task"}:
            continue

        filtered.append(ent)

    return filtered

if __name__ == "__main__":
    # --- 测试 ---
    # 模拟从 NER 来的嘈杂数据
    test_entities = [
        {"name": "RDF", "label": "Concept"},
        {"name": "R.D.F.", "label": "Concept"},
        {"name": "知识图谱", "label": "Concept"},
        {"name": "spaCy", "label": "Technology"},
        {"name": "张三", "label": "PERSON"}  # PER 不会被融合
    ]

    test_relations = [
        {"head": "R.D.F.", "head_label": "Concept", "type": "IS_A", "tail": "知识图谱", "tail_label": "Concept"},
        {"head": "R.D.F.", "head_label": "Concept", "type": "IS_A", "tail": "知识图谱", "tail_label": "Concept"}  # 重复关系
    ]

    print("--- 1. 创建规范化 Map ---")
    cmap = create_canonical_map(test_entities, similarity_threshold=0.8)
    print(f"Map: {cmap}")

    print("\n--- 2. 解析实体和关系 ---")
    # final_ents, final_rels = resolve_entities_and_relations(test_entities, test_relations, cmap)

    final_ents = resolve_entities(test_entities, cmap)
    final_rels = resolve_relations(test_relations, cmap)

    print(f"解析后的实体: {final_ents}")
    print(f"解析后的关系: {final_rels}")

    # 预期实体: (RDF, 知识图谱, spaCy, 张三)
    # 预期关系: (RDF -IS_A-> 知识图谱)