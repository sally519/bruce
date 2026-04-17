"""PRD 生成节点 (DocNode)

这是一个子图，包含：
1. 文件扫描和内容提取
2. DocAgent 生成 PRD 草稿
3. ReviewAgent 审核 PRD
4. 循环修改直到通过
"""

from typing import Dict, Any
from langgraph.runtime import Runtime

from agent.state import WorkflowState, WorkflowContext
from graphs.subgraphs.doc_subgraph import doc_subgraph, DocNodeName


class DocNode:
    """PRD 生成节点

    调用 PRD 生成子图处理需求文档
    """

    @staticmethod
    async def call(state: WorkflowState, runtime: Runtime[WorkflowContext]) -> Dict[str, Any]:
        """执行 PRD 生成子图

        输入目录默认: D:/pyProject/bruce_project_flow/doc/requestion
        输出目录: D:/pyProject/bruce_project_flow/doc/output
        """
        # 默认输入目录
        input_directory = state.get("input_directory", "D:/pyProject/bruce_project_flow/doc/requestion")

        # 调用子图
        result = await doc_subgraph.ainvoke({
            "input_directory": input_directory,
            "prd_version": 0,
            "review_iterations": 0,
        })

        return {
            "prd_content": result.get("final_prd", ""),
            "prd_review_result": "approved" if result.get("success") else "rejected",
            "prd_review_feedback": result.get("review_comments", ""),
        }
