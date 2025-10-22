# 文本清洗
import fitz  # PyMuPDF 库
import os
from kg_course_project.utils.logger import get_logger

logger = get_logger(__name__)


def extract_text_from_pdf(pdf_path):
    """
    从指定的 PDF 文件中提取所有文本。

    :param pdf_path: PDF 文件的路径
    :return: 提取的全部文本，如果失败则返回 None
    """
    if not os.path.exists(pdf_path):
        logger.error(f"PDF 文件未找到: {pdf_path}")
        return None

    full_text = []

    try:
        # 打开 PDF 文件
        doc = fitz.open(pdf_path)

        logger.info(f"正在解析 PDF: {pdf_path}, 共 {doc.page_count} 页。")

        # 遍历每一页
        for page_num in range(doc.page_count):
            page = doc.load_page(page_num)
            text = page.get_text("text")  # 提取纯文本
            full_text.append(text)

        doc.close()

        return "\n".join(full_text)

    except fitz.errors.EmptyFileError:
        logger.error(f"PDF 文件为空或已损坏: {pdf_path}")
    except Exception as e:
        logger.error(f"解析 PDF 时发生未知错误 {pdf_path}: {e}")

    return None


if __name__ == "__main__":
    # --- 测试 ---
    # 你需要自己准备一个 PDF 文件放在 data/raw/ 目录下
    # 这里我们假设你有一个 'syllabus.pdf'

    # (为了让测试能运行，我们先创建一个假的 PDF)
    test_pdf_path = os.path.join("..", "data", "raw", "test_syllabus.pdf")

    # 创建一个简单的测试 PDF (如果它不存在)
    if not os.path.exists(test_pdf_path):
        try:
            os.makedirs(os.path.dirname(test_pdf_path), exist_ok=True)
            doc = fitz.open()  # 创建新 PDF
            page = doc.new_page()
            page.insert_text((72, 72), "第一章：知识表示", fontsize=16)
            page.insert_text((72, 90), "本章包含：RDF 和 RDFS。")
            page.insert_text((72, 720), "Page 1")  # 模拟页脚
            doc.save(test_pdf_path)
            doc.close()
            print(f"已创建测试 PDF: {test_pdf_path}")
        except Exception as e:
            print(f"创建测试 PDF 失败: {e}")

    # 运行解析
    print(f"\n--- 正在测试解析: {test_pdf_path} ---")
    pdf_text = extract_text_from_pdf(test_pdf_path)

    if pdf_text:
        print(f"成功获取文本:\n{pdf_text}")

        # 测试与清理器集成
        from kg_course_project.data_acquisition.data_cleaner import clean_text_pipeline

        print("\n--- 清理后 ---")
        cleaned_text = clean_text_pipeline(pdf_text)
        print(cleaned_text)
    else:
        print("解析 PDF 失败。")