"""差异比对分析节点 (Diff-Agent)

对比新旧需求差异
"""

from typing import Dict, Any
from langgraph.runtime import Runtime

from agent.state import WorkflowState, WorkflowContext


class DiffNode:
    """差异比对分析节点"""

    @staticmethod
    async def call(state: WorkflowState, runtime: Runtime[WorkflowContext]) -> Dict[str, Any]:
        """分析需求差异"""
        # TODO: 调用 LLM 分析差异
        delta_analysis = {}

        return {
            "delta_analysis": delta_analysis,
        }
