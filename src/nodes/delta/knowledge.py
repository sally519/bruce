"""历史需求提取节点 (Knowledge-Agent)

从知识库中提取相关历史需求
"""

from typing import Dict, Any
from langgraph.runtime import Runtime

from agent.state import WorkflowState, WorkflowContext
from nodes.base import BaseNode


class KnowledgeNode:
    """历史需求提取节点"""

    @staticmethod
    async def call(state: WorkflowState, runtime: Runtime[WorkflowContext]) -> Dict[str, Any]:
        """从知识库提取历史需求"""
        requirement_id = state.get("requirement_id", "")

        # TODO: 查询知识库获取相关历史需求
        history_requirements = []

        return {
            "history_requirements": history_requirements,
        }
