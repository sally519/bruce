"""测试用例生成节点 (Test-Agent)"""

from typing import Dict, Any
from langgraph.runtime import Runtime

from agent.state import WorkflowState, WorkflowContext


class TestNode:
    """测试用例生成节点"""

    @staticmethod
    async def call(state: WorkflowState, runtime: Runtime[WorkflowContext]) -> Dict[str, Any]:
        """生成测试用例"""
        # TODO: 调用 LLM 生成测试用例
        test_cases = []
        return {"test_cases": test_cases}
