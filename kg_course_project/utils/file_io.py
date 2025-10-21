# 文件读写帮助函数
import yaml
import json

def read_yaml(file_path):
    """读取 YAML 配置文件"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def read_file(file_path):
    """读取文本文件"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()

def save_json(data, file_path):
    """保存数据为 JSON"""
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)