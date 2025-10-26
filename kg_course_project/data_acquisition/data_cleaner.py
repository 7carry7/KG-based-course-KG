# 文本清洗
import re
import unicodedata
from html import unescape
from collections import Counter
try:
    from bs4 import BeautifulSoup
    BEAUTIFULSOUP_AVAILABLE = True
except ImportError:
    BEAUTIFULSOUP_AVAILABLE = False


def normalize_unicode(text):
    """
    处理 Unicode 字符，例如将 'ﬁ' 转换为 'fi'，并使用 NFC 范式。
    """
    return unicodedata.normalize('NFC', text)


def remove_html_tags(text, method='beautifulsoup', replace_with=' '):
    """
    安全高效地移除 HTML 标签

    参数:
        text: 输入文本
        method: 清理方法 ('auto', 'beautifulsoup', 'regex', 'html_parser')
        replace_with: 替换标签的字符 (默认空格)

    返回:
        清理后的纯文本
    """
    if not text or not isinstance(text, str):
        return text

    # 预处理：解码 HTML 实体
    text = unescape(text.strip())

    if method == 'auto':
        method = _choose_best_method(text)

    if method == 'beautifulsoup' and BEAUTIFULSOUP_AVAILABLE:
        return _remove_with_beautifulsoup(text, replace_with)
    elif method == 'html_parser':
        return _remove_with_html_parser(text, replace_with)
    else:
        return _remove_with_regex(text, replace_with)


def _choose_best_method(text):
    """根据内容选择最佳清理方法"""
    if not BEAUTIFULSOUP_AVAILABLE:
        return 'regex'

    # 简单内容用正则，复杂内容用 BeautifulSoup
    tag_count = text.count('<')
    if tag_count < 3 and len(text) < 1000:
        return 'regex'
    elif 'script' in text.lower() or 'style' in text.lower():
        return 'beautifulsoup'
    else:
        return 'beautifulsoup'


def _remove_with_beautifulsoup(text, replace_with=' '):
    """使用 BeautifulSoup 安全移除 HTML 标签"""
    try:
        soup = BeautifulSoup(text, 'html.parser')

        # 移除脚本和样式标签
        for script in soup(["script", "style"]):
            script.decompose()

        # 获取文本并处理空白字符
        text = soup.get_text()
        text = _normalize_whitespace(text, replace_with)
        return text
    except Exception:
        # 如果 BeautifulSoup 失败，回退到正则表达式
        return _remove_with_regex(text, replace_with)


def _remove_with_html_parser(text, replace_with=' '):
    """使用标准库的 HTMLParser (无依赖)"""
    try:
        from html.parser import HTMLParser

        class HTMLTextExtractor(HTMLParser):
            def __init__(self):
                super().__init__()
                self.result = []
                self.ignore_tags = {'script', 'style'}
                self.current_tag = None

            def handle_starttag(self, tag, attrs):
                self.current_tag = tag.lower()
                if tag in self.ignore_tags:
                    self.result.append(replace_with)

            def handle_endtag(self, tag):
                self.current_tag = None
                self.result.append(replace_with)

            def handle_data(self, data):
                if self.current_tag not in self.ignore_tags:
                    self.result.append(data)

        extractor = HTMLTextExtractor()
        extractor.feed(text)
        result = ''.join(extractor.result)
        return _normalize_whitespace(result, replace_with)
    except Exception:
        return _remove_with_regex(text, replace_with)


def _remove_with_regex(text, replace_with=' '):
    """使用优化的正则表达式方法"""
    # 优化的正则表达式模式
    patterns = [
        # 移除注释
        r'<!--.*?-->',
        # 移除脚本和样式标签及其内容
        r'<(script|style).*?>.*?</\1>',
        # 移除其他标签（更安全的模式）
        r'<[^>]+>',
        # 移除 doctype 声明
        r'<!DOCTYPE[^>]*>',
        # 移除 XML 声明
        r'<\?xml[^>]*\?>'
    ]

    cleaned_text = text
    for pattern in patterns:
        try:
            cleaned_text = re.sub(pattern, replace_with, cleaned_text, flags=re.DOTALL | re.IGNORECASE)
        except re.error:
            continue

    return _normalize_whitespace(cleaned_text, replace_with)


def _normalize_whitespace(text, replace_with=' '):
    """规范化空白字符"""
    # 合并连续的替换字符
    if replace_with == ' ':
        text = re.sub(r'\s+', ' ', text)
    else:
        # 避免连续的特殊替换字符
        text = re.sub(f'{re.escape(replace_with)}+', replace_with, text)

    return text.strip()


# 便捷的快捷函数
def remove_html_tags_fast(text):
    """快速版本，自动选择最快的方法"""
    return remove_html_tags(text, method='auto')


def remove_html_tags_safe(text):
    """安全版本，优先使用 BeautifulSoup"""
    return remove_html_tags(text, method='beautifulsoup')


def remove_html_tags_light(text):
    """轻量版本，无外部依赖"""
    return remove_html_tags(text, method='html_parser')

# def remove_html_tags(text):
#     """
#     使用正则表达式移除残留的 HTML 标签。
#     (注: BeautifulSoup 应该是首选，这只是一个后备清理)
#     """
#     cleanr = re.compile('<.*?>')
#     return re.sub(cleanr, ' ', text)


def remove_urls(text):
    """移除文本中的 http/https/ftp/www 链接"""
    # # 广义的 URL 匹配
    # url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
    # # 匹配 www. 开头
    # www_pattern = r'www\.(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
    # text = re.sub(url_pattern, ' ', text)
    # text = re.sub(www_pattern, ' ', text)
    # return text
    """移除URL并清理多余空格"""
    url_pattern = r'(?:https?|ftp)://[^\s]+|www\.[^\s]+'
    text = re.sub(url_pattern, ' ', text)
    # 将多个连续空格合并为一个
    text = re.sub(r'\s+', ' ', text)
    return text.strip()



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
    """
    """
    移除 PDF 解析时常见的残留物，如页眉、页脚、页码。
    (这是一个简化的示例)
    """
    # 移除各种页码格式
    patterns = [
        r'Page\s+\d+',  # 英文页码
        r'第\s*\d+\s*页',  # 中文页码
        r'-\s*\d+\s*-',  # 被横线包围的页码
        r'^\s*\d+\s*/\s*\d+\s*$',  # 分数格式页码 "1/10"
        r'^\s*\d+\s*$',  # 单独的数字行
        r'^\s*[ivxlcdm]+\s*$',  # 罗马数字页码
        r'\[\d+\]',  # [1], [2] 等简单引用
        r'\[\d+,\s?\d+\]',  # [1,2], [1, 2] 等多引用
        r'\[\d+-\d+\]',  # [1-3], [5-10] 等范围引用
        r'\(\d+\)',  # (1), (2) 等括号引用
        r'\(\d+,\s?\d+\)',  # (1,2), (1, 2) 等
        r'\(\d+-\d+\)',  # (1-3), (5-10) 等
        r'^\s*\[\d+\]\s*$',  # 单独成行的引用标记
        r'^\s*\(\d+\)\s*$',  # 单独成行的括号引用
        r'^\s*[•·▪➢➤\-]\s*',  # 各种项目符号
        r'^\s*\d+\.\s*',  # 数字加点
        r'^\s*[a-zA-Z]\.\s*',  # 字母加点
    ]

    for pattern in patterns:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE | re.MULTILINE)

    # 清理多余的空行（连续两个以上的换行符替换为一个）
    text = re.sub(r'\n\s*\n+', '\n\n', text).strip()
    # 移除URL
    text = remove_urls(text)

    #  统一空白字符
    text = re.sub(r'\s+', ' ', text)  # 合并多个空白字符
    text = re.sub(r'\n +', '\n', text)  # 移除行首空格

    return text.strip()

def clean_text_pipeline(text, lowercase=False):
    """
    运行一个完整的文本清理流程。

    :param text: 原始输入文本 (可能来自 HTML 或 PDF)
    :param lowercase: 是否将所有文本转为小写 (对实体识别可能有害)
    :return: 清理后的文本
    """
    # 1. 解码 HTML 实体
    text = unescape(text)

    # 2. 移除 HTML 标签
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
    4
    """
    #
    print("--- HTML 清理测试 ---")
    cleaned_html = clean_text_pipeline(raw_html_text)
    print(cleaned_html)

    print("\n--- PDF 清理测试 ---")
    cleaned_pdf = clean_text_pipeline(raw_pdf_text)
    print(cleaned_pdf)