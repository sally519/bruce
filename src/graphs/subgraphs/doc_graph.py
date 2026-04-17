"""DocNode 子图状态定义

包含 PRD 生成子图的状态结构
"""

from typing import TypedDict, Optional, List, Dict, Any
from enum import Enum


class ReviewStatus(str, Enum):
    """审核状态"""
    PENDING = "pending"      # 待审核
    APPROVED = "approved"   # 通过
    REJECTED = "rejected"   # 需修改


class DocSubGraphState(TypedDict, total=False):
    """DocNode 子图状态

    包含文档处理、PRD 生成和审核的完整流程状态
    """
    # 输入文件信息
    input_directory: str                    # 输入文件目录
    files: Optional[List[Dict[str, Any]]]   # 扫描到的文件列表

    # 文件内容
    file_contents: Optional[List[Dict[str, Any]]]  # 提取的文件内容

    # PRD 内容
    prd_draft: Optional[str]                # PRD 草稿内容
    prd_version: int                        # PRD 版本号

    # 用户介入相关
    needs_user_input: bool                 # 是否需要用户介入
    user_input_prompt: Optional[str]       # 提示用户需要补充的内容
    user_input: Optional[str]               # 用户补充的内容
    user_input_files: Optional[List[Dict[str, Any]]]  # 用户补充的文件内容
    input_request_count: int               # 请求用户输入的次数
    user_input_requested: bool            # 是否已经请求过用户输入（限制最多一次）

    # 审核信息
    review_status: ReviewStatus             # 审核状态
    review_comments: Optional[str]         # 审核意见
    review_score: Optional[float]          # 审核评分 (0-100)
    review_iterations: int                  # 审核迭代次数

    # 最终输出
    final_prd: Optional[str]                # 最终通过的 PRD
    output_path: Optional[str]              # 输出文件路径
    success: bool                           # 是否成功完成
