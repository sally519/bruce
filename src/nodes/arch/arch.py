"""架构设计节点 (Arch-Agent)

生成技术架构方案
"""

from typing import Dict, Any
from langgraph.runtime import Runtime

from agent.state import WorkflowState, WorkflowContext


class ArchNode:
    """架构设计节点"""

    @staticmethod
    async def call(state: WorkflowState, runtime: Runtime[WorkflowContext]) -> Dict[str, Any]:
        """生成架构方案"""
        # TODO: 调用 LLM 生成架构设计
        architecture_design = "# 架构设计文档"

        return {
            "architecture_design": architecture_design,
        }
