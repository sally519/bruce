"""影响范围评估节点 (Impact-Agent)

评估变更对现有系统的影响范围
"""

from typing import Dict, Any
from langgraph.runtime import Runtime

from agent.state import WorkflowState, WorkflowContext


class ImpactNode:
    """影响范围评估节点"""

    @staticmethod
    async def call(state: WorkflowState, runtime: Runtime[WorkflowContext]) -> Dict[str, Any]:
        """评估影响范围"""
        # TODO: 调用 LLM 评估影响
        impact_assessment = {}

        return {
            "impact_assessment": impact_assessment,
        }
