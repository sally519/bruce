"""PRD 生成节点 (Doc-Agent)

自动根据需求生成产品需求文档（PRD）
"""

from typing import Dict, Any
from langgraph.runtime import Runtime

from agent.state import WorkflowState, WorkflowContext
from nodes.base import BaseNode


class DocNode(BaseNode):
    """PRD 生成节点

    根据需求标题和描述，自动生成完整的 PRD 文档
    """

    async def call(self, state: WorkflowState, runtime: Runtime[WorkflowContext]) -> Dict[str, Any]:
        """生成 PRD 文档"""
        requirement_title = state.get("requirement_title", "")
        requirement_id = state.get("requirement_id", "")

        # TODO: 调用 LLM 生成 PRD
        # 这里先返回占位内容
        prd_content = f"""# PRD - {requirement_title}

## 1. 背景与目标

## 2. 功能需求

## 3. 非功能需求

## 4. 验收标准

## 5. 排期计划
"""

        return {
            "prd_content": prd_content,
        }


class DocNode:
    """PRD 生成节点静态方法封装"""

    @staticmethod
    async def call(state: WorkflowState, runtime: Runtime[WorkflowContext]) -> Dict[str, Any]:
        """生成 PRD 文档"""
        requirement_title = state.get("requirement_title", "")
        requirement_id = state.get("requirement_id", "")

        # TODO: 调用 LLM 生成 PRD
        prd_content = f"""# PRD - {requirement_title}

## 1. 背景与目标

## 2. 功能需求

## 3. 非功能需求

## 4. 验收标准

## 5. 排期计划
"""

        return {
            "prd_content": prd_content,
        }
