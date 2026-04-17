"""工作流状态和上下文定义

本模块定义了企业研发流程 AI 自动化系统的核心数据类型
"""

from typing import TypedDict, Optional, Dict, Any, List
from enum import Enum


class RequirementType(str, Enum):
    """需求类型"""
    NEW = "new"           # 全新需求
    ITERATION = "iteration"  # 迭代需求


class ReviewResult(str, Enum):
    """审核结果"""
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


class WorkflowState(TypedDict, total=False):
    """主工作流状态

    包含完整的研发流程所有阶段的数据
    """
    # 基础信息
    requirement_id: str                    # 需求ID
    requirement_title: str                # 需求标题
    requirement_type: RequirementType     # 需求类型
    created_at: str                        # 创建时间

    # PRD 相关
    prd_content: Optional[str]            # PRD 文档内容
    prd_review_result: Optional[ReviewResult]  # PRD 审核结果
    prd_review_feedback: Optional[str]     # 审核反馈

    # 差量分析相关（迭代需求）
    history_requirements: Optional[List[Dict]]  # 历史需求
    delta_analysis: Optional[Dict]         # 差量分析结果
    impact_assessment: Optional[Dict]     # 影响范围评估
    delta_document: Optional[str]          # 差量文档

    # 架构设计相关
    architecture_design: Optional[str]     # 架构方案
    arch_review_result: Optional[ReviewResult]
    arch_review_feedback: Optional[str]

    # 开发相关
    web_code: Optional[str]               # Web端代码
    h5_code: Optional[str]                 # H5端代码
    mobile_code: Optional[str]            # 移动端代码
    api_code: Optional[str]               # 后端API代码
    dev_review_result: Optional[ReviewResult]
    dev_review_feedback: Optional[str]

    # QA 相关
    qa_report: Optional[Dict]              # QA 自检报告
    fix_count: int                         # 修复次数
    max_fix_attempts: int                 # 最大修复尝试次数

    # 测试相关
    test_cases: Optional[List[Dict]]       # 测试用例
    test_review_result: Optional[ReviewResult]
    test_report: Optional[Dict]           # 测试报告
    debug_result: Optional[Dict]          # 问题定位结果

    # 部署相关
    deploy_status: Optional[str]           # 部署状态
    gray_release_ok: bool                 # 灰度验证结果

    # 最终结果
    final_result: Optional[ReviewResult]  # 最终审核结果
    archived: bool                        # 是否已归档


class WorkflowContext(TypedDict, total=False):
    """工作流运行时上下文配置

    用于配置每个 assistant 实例的行为参数
    """
    # LLM 配置
    model_name: str                        # 模型名称
    temperature: float                     # 温度参数

    # 飞书集成配置
    feishu_webhook: Optional[str]         # 飞书 Webhook
    feishu_approval_token: Optional[str]  # 审批 Token

    # 代码仓库配置
    repo_url: Optional[str]               # 仓库地址
    repo_branch: str                       # 分支名

    # 部署配置
    deploy_env: str                        # 部署环境
    deploy_namespace: str                  # 命名空间

    # 检查点配置
    checkpointer: Any                     # 状态持久化


class WorkflowConfig:
    """工作流配置管理"""

    DEFAULT_MODEL = "gpt-4"
    DEFAULT_TEMPERATURE = 0.7
    MAX_FIX_ATTEMPTS = 3

    @classmethod
    def get_default_context(cls) -> WorkflowContext:
        """获取默认上下文配置"""
        return WorkflowContext(
            model_name=cls.DEFAULT_MODEL,
            temperature=cls.DEFAULT_TEMPERATURE,
            repo_branch="main",
            deploy_env="staging",
            deploy_namespace="default",
            max_fix_attempts=cls.MAX_FIX_ATTEMPTS,
        )
