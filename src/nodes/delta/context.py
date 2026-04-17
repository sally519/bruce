"""差量文档生成节点 (Context-Agent)

生成完整的差量需求文档
"""

from typing import Dict, Any
from langgraph.runtime import Runtime

from agent.state import WorkflowState, WorkflowContext


class ContextNode:
    """差量文档生成节点"""

    @staticmethod
    async def call(state: WorkflowState, runtime: Runtime[WorkflowContext]) -> Dict[str, Any]:
        """生成差量文档"""
        # TODO: 调用 LLM 生成差量文档
        delta_document = "# 差量文档"

        return {
            "delta_document": delta_document,
        }
