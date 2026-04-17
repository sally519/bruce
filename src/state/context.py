"""工作流上下文定义"""
from typing import Optional, Dict, Any
from langgraph.checkpoint.base import BaseCheckpointSaver


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
    checkpointer: Optional[BaseCheckpointSaver]  # 状态持久化


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
