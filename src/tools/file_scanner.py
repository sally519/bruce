"""文件扫描工具

扫描指定目录下的文件，支持 PDF、Word、图片、Markdown 格式
"""

import os
from pathlib import Path
from typing import List, Dict, Any


SUPPORTED_EXTENSIONS = {
    ".pdf": "pdf",
    ".docx": "word",
    ".doc": "word",
    ".png": "image",
    ".jpg": "image",
    ".jpeg": "image",
    ".md": "markdown",
}


def scan_files(directory: str) -> List[Dict[str, Any]]:
    """扫描目录下的所有支持的文件

    Args:
        directory: 要扫描的目录路径

    Returns:
        文件信息列表，每个文件包含：
        - path: 文件完整路径
        - name: 文件名
        - type: 文件类型 (pdf/word/image/markdown)
        - size: 文件大小（字节）
    """
    files = []
    dir_path = Path(directory)

    if not dir_path.exists():
        return files

    for file_path in dir_path.iterdir():
        if file_path.is_file():
            ext = file_path.suffix.lower()
            if ext in SUPPORTED_EXTENSIONS:
                files.append({
                    "path": str(file_path.absolute()),
                    "name": file_path.name,
                    "type": SUPPORTED_EXTENSIONS[ext],
                    "size": file_path.stat().st_size,
                })

    return files
