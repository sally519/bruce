"""文件内容提取工具

从不同格式的文件中提取文本内容
"""

import io
from typing import Dict, Any

# PDF 处理
try:
    import pypdf
    HAS_PDF = True
except ImportError:
    HAS_PDF = False

# Word 处理
try:
    from docx import Document
    HAS_DOCX = True
except ImportError:
    HAS_DOCX = False

# 图片处理（OCR）
try:
    from PIL import Image
    import pytesseract
    HAS_OCR = True
except ImportError:
    HAS_OCR = False


def extract_text_from_pdf(file_path: str) -> str:
    """从 PDF 文件提取文本

    Args:
        file_path: PDF 文件路径

    Returns:
        提取的文本内容
    """
    if not HAS_PDF:
        raise ImportError("pypdf 未安装，请运行: pip install pypdf")

    text_parts = []
    with open(file_path, "rb") as f:
        reader = pypdf.PdfReader(f)
        for page_num, page in enumerate(reader.pages):
            text = page.extract_text()
            if text:
                text_parts.append(f"[页面 {page_num + 1}]\n{text}")

    return "\n\n".join(text_parts)


def extract_text_from_word(file_path: str) -> str:
    """从 Word 文档提取文本

    Args:
        file_path: Word 文件路径

    Returns:
        提取的文本内容
    """
    if not HAS_DOCX:
        raise ImportError("python-docx 未安装，请运行: pip install python-docx")

    doc = Document(file_path)
    paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
    return "\n\n".join(paragraphs)


def extract_text_from_image(file_path: str) -> str:
    """从图片提取文本（OCR）

    Args:
        file_path: 图片文件路径

    Returns:
        提取的文本内容
    """
    if not HAS_OCR:
        raise ImportError("pytesseract 或 Pillow 未安装，请运行: pip install pytesseract pillow")

    image = Image.open(file_path)
    text = pytesseract.image_to_string(image, lang="chi_sim+eng")
    return text


def extract_text_from_markdown(file_path: str) -> str:
    """从 Markdown 文件提取文本

    Args:
        file_path: Markdown 文件路径

    Returns:
        文件内容
    """
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()


def extract_file_content(file_path: str) -> Dict[str, Any]:
    """根据文件类型提取内容

    Args:
        file_path: 文件路径

    Returns:
        包含类型和内容的字典
    """
    from pathlib import Path

    ext = Path(file_path).suffix.lower()

    if ext == ".pdf":
        content = extract_text_from_pdf(file_path)
        file_type = "pdf"
    elif ext in [".docx", ".doc"]:
        content = extract_text_from_word(file_path)
        file_type = "word"
    elif ext in [".png", ".jpg", ".jpeg"]:
        content = extract_text_from_image(file_path)
        file_type = "image"
    elif ext == ".md":
        content = extract_text_from_markdown(file_path)
        file_type = "markdown"
    else:
        raise ValueError(f"不支持的文件类型: {ext}")

    return {
        "type": file_type,
        "content": content,
        "path": file_path,
    }
