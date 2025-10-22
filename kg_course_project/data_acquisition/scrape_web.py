# 爬取课程网页
import requests
from bs4 import BeautifulSoup
from kg_course_project.utils.logger import get_logger

logger = get_logger(__name__)


def fetch_webpage_text(url):
    """
    爬取指定 URL 的网页，并智能提取主要文本内容。

    :param url: 目标网页 URL
    :return: 提取的文本内容，如果失败则返回 None
    """

    # 设置一个真实的 User-Agent，防止被网站屏蔽
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        # 如果请求失败 (如 404, 500), 抛出异常
        response.raise_for_status()

        # 使用 BeautifulSoup 解析 HTML
        soup = BeautifulSoup(response.text, 'html.parser')

        # 1. 移除脚本和样式元素，它们包含大量无用文本
        for element in soup(["script", "style", "nav", "footer", "aside"]):
            element.decompose()  # 移除该标签

        # 2. 尝试智能提取主要内容
        # 这是一个启发式规则：
        # 现代网页通常使用 <article> 或 <main> 标签包裹主要内容
        main_content = soup.find('article')
        if not main_content:
            main_content = soup.find('main')

        # 3. 如果找不到 <article> 或 <main>，退而求其次：
        # 查找 ID 为 "content" 或 class 为 "content" 的 div
        if not main_content:
            main_content = soup.find(id='content')
        if not main_content:
            main_content = soup.find(class_='content')

        # 4. 如果还是找不到，就使用整个 <body>
        if not main_content:
            main_content = soup.body
            if not main_content:  # 极端情况
                return None

        # 5. 从主要内容中提取所有段落 <p> 的文本
        paragraphs = main_content.find_all('p')
        if paragraphs:
            text = '\n'.join([p.get_text(strip=True) for p in paragraphs])
        else:
            # 如果没有 <p> 标签，就获取 main_content 的所有文本
            text = main_content.get_text(separator='\n', strip=True)

        logger.info(f"成功爬取并解析 URL: {url}")
        return text

    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP 错误，爬取失败 {url}: {e}")
    except requests.exceptions.RequestException as e:
        logger.error(f"请求错误，爬取失败 {url}: {e}")
    except Exception as e:
        logger.error(f"解析 HTML 时发生未知错误 {url}: {e}")

    return None


if __name__ == "__main__":
    # --- 测试 ---
    # 使用一个维基百科页面作为示例
    test_url = "https://zh.wikipedia.org/wiki/知识图谱"

    print(f"--- 正在测试爬取: {test_url} ---")
    web_text = fetch_webpage_text(test_url)

    if web_text:
        print(f"成功获取文本 (前 500 字符): \n{web_text[:500]}...")

        # 测试与清理器集成
        from kg_course_project.data_acquisition.data_cleaner import clean_text_pipeline

        print("\n--- 清理后 (前 500 字符) ---")
        cleaned_text = clean_text_pipeline(web_text)
        print(cleaned_text[:500] + "...")
    else:
        print("爬取失败。")