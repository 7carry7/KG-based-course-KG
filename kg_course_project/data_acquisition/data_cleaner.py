# 文本清洗
import re

def simple_clean(text):
    """非常简单的文本清洗"""
    text = text.replace('\n', ' ') # 替换换行符
    text = re.sub(r'\s+', ' ', text) # 正则表达式模式，匹配任何空白字符（空格、制表符、换行符等）
    text = text.strip() # 去除首尾空格
    return text