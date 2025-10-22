# 文本清洗
import re
import unicodedata
from html import unescape


def normalize_unicode(text):
    """
    处理 Unicode 字符，例如将 'ﬁ' 转换为 'fi'，并使用 NFC 范式。
    """
    return unicodedata.normalize('NFC', text)


def remove_html_tags(text):
    """
    使用正则表达式移除残留的 HTML 标签。
    (注: BeautifulSoup 应该是首选，这只是一个后备清理)
    """
    cleanr = re.compile('<.*?>')
    return re.sub(cleanr, ' ', text)


def remove_urls(text):
    """移除文本中的 http/https/ftp/www 链接"""
    # 广义的 URL 匹配
    url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
    # 匹配 www. 开头
    www_pattern = r'www\.(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
    text = re.sub(url_pattern, ' ', text)
    text = re.sub(www_pattern, ' ', text)
    return text


def normalize_punctuation(text):
    """
    将非标准的标点符号（如智能引号）转换回标准 ASCII。
    这对基于规则的抽取非常重要。
    """
    replacements = {
        '“': '"', '”': '"',  # 中文/智能双引号
        '‘': "'", '’': "'",  # 中文/智能单引号
        '（': '(', '）': ')',  # 中文括号
        '：': ':',  # 中文冒号
        '，': ',',  # 中文逗号
        '；': ';',  # 中文分号
        '。': '.',  # 中文句号
        '？': '?',  # 中文问号
        '！': '!',  # 中文叹号
        '—': '-',  # 长破折号
        '…': '...',  # 省略号
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text


def remove_extra_whitespace(text):
    """
    移除多余的空格、换行符和制表符。
    """
    text = text.replace('\n', ' ')  # 替换换行符为空格
    text = text.replace('\t', ' ')  # 替换制表符为空格
    text = re.sub(r'\s+', ' ', text)  # 将多个空格合并为一个
    return text.strip()  # 去除首尾空格


def remove_pdf_artifacts(text):
    """
    移除 PDF 解析时常见的残留物，如页眉、页脚、页码。
    (这是一个简化的示例)
    """
    # 移除 "Page X" 或 "第 X 页"
    text = re.sub(r'Page\s+\d+', ' ', text, flags=re.IGNORECASE)
    text = re.sub(r'第\s*\d+\s*页', ' ', text)
    # 移除单独的数字（可能是页码）
    text = re.sub(r'^\s*\d+\s*$', '', text, flags=re.MULTILINE)
    return text


def clean_text_pipeline(text, lowercase=False):
    """
    运行一个完整的文本清理流程。

    :param text: 原始输入文本 (可能来自 HTML 或 PDF)
    :param lowercase: 是否将所有文本转为小写 (对实体识别可能有害)
    :return: 清理后的文本
    """
    # 1. 解码 HTML 实体 (例如 &amp; -> &)
    text = unescape(text)

    # 2. 移除 HTML 标签 (如果 BeautifulSoup 没清干净)
    text = remove_html_tags(text)

    # 3. 移除链接
    text = remove_urls(text)

    # 4. 规范化 Unicode
    text = normalize_unicode(text)

    # 5. 规范化标点符号 (对中文和英文都重要)
    text = normalize_punctuation(text)

    # 6. 移除 PDF 特有的残留物
    text = remove_pdf_artifacts(text)

    # 7. 移除多余的空白
    text = remove_extra_whitespace(text)

    # 8. (可选) 转为小写
    if lowercase:
        text = text.lower()

    return text


# --- (保留旧的 simple_clean 以防万一，但推荐使用 pipeline) ---
def simple_clean(text):
    """(旧版) 非常简单的文本清洗"""
    text = text.replace('\n', ' ')  # 替换换行符
    text = re.sub(r'\s+', ' ', text)  # 替换多个空格
    text = text.strip()  # 去除首尾空格
    return text


if __name__ == "__main__":
    # --- 测试 ---
    raw_html_text = """
    <html><head><title>Test</title></head><body>
    <h1>第一章：知识表示</h1>
    <p>
      本章包含的概念有：“RDF”，“RDFS” 和 <a href="http://example.com">OWL</a>。
      详情请访问 www.w3.org
    </p>
    <p>
      Page 1
    </p>
    </body></html>
    """

    raw_pdf_text = """
    一个概念“TransE”...
    它需要 RDFS。

    2

    第 3 页
    """

    print("--- HTML 清理测试 ---")
    cleaned_html = clean_text_pipeline(raw_html_text)
    print(cleaned_html)

    print("\n--- PDF 清理测试 ---")
    cleaned_pdf = clean_text_pipeline(raw_pdf_text)
    print(cleaned_pdf)