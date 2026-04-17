"""LangGraph 主工作流图定义

完整工作流程:
1. PRD 生成与审核
2. 差量分析（迭代需求专用）
3. 架构方案与审核
4. 多端并行开发
5. 代码自检与自动修复
6. 开发结果人工评审
7. 测试用例生成与审核
8. 自动化测试与问题定位
9. 部署与灰度验证
10. 流程归档
"""

from __future__ import annotations

from typing import Dict, Any, Literal
from langgraph.graph import StateGraph, END
from langgraph.runtime import Runtime
from langgraph.checkpoint.memory import MemorySaver

from agent.state import WorkflowState, WorkflowContext
from nodes.prd import DocNode
from nodes.delta import KnowledgeNode, DiffNode, ImpactNode, ContextNode
from nodes.arch import ArchNode
from nodes.dev import WebNode, H5Node, MobileNode, APINode
from nodes.qa import QANode, FixNode
from nodes.test import TestNode, TestRunnerNode, DebugNode
from nodes.deploy import DeployNode, CheckNode
from nodes.archive import StoreNode


# 节点名称常量
class NodeName:
    """工作流节点名称"""
    # PRD 节点
    DOC = "doc"
    PRD_REVIEW = "prd_review"

    # 差量分析子图节点
    KNOWLEDGE = "knowledge"
    DIFF = "diff"
    IMPACT = "impact"
    CONTEXT = "context"

    # 架构节点
    ARCH = "arch"
    ARCH_REVIEW = "arch_review"

    # 开发节点
    WEB = "web"
    H5 = "h5"
    MOBILE = "mobile"
    API = "api"
    DEV_REVIEW = "dev_review"

    # QA 节点
    QA = "qa"
    FIX = "fix"

    # 测试节点
    TEST = "test"
    TEST_REVIEW = "test_review"
    TEST_RUNNER = "test_runner"
    DEBUG = "debug"

    # 部署节点
    DEPLOY = "deploy"
    CHECK = "check"

    # 归档节点
    STORE = "store"


def create_workflow_graph() -> StateGraph:
    """创建主工作流图

    工作流程:
    开始 -> PRD生成 -> PRD审核 -> [需求类型判断]
                                    |
                                    ├-> [迭代需求] -> 差量子图 -> 架构设计 -> 架构审核 -> ...
                                    |
                                    └-> [全新需求] -> 架构设计 -> 架构审核 -> ...

    后续流程:
    架构审核通过 -> 多端并行开发 -> 代码自检 -> [自检通过?] -> 开发评审 -> 测试用例 -> 测试审核
                                                                          |
                                                                          └-> [测试执行] -> [测试通过?] -> 部署 -> 灰度验证 -> 归档 -> 结束
    """
    # 创建状态图
    graph = StateGraph(WorkflowState, context_schema=WorkflowContext)

    # 添加所有节点
    # PRD 相关
    graph.add_node(NodeName.DOC, DocNode.call)
    graph.add_node(NodeName.PRD_REVIEW, human_review_node)

    # 差量分析子图节点（按顺序执行）
    graph.add_node(NodeName.KNOWLEDGE, KnowledgeNode.call)
    graph.add_node(NodeName.DIFF, DiffNode.call)
    graph.add_node(NodeName.IMPACT, ImpactNode.call)
    graph.add_node(NodeName.CONTEXT, ContextNode.call)

    # 架构相关
    graph.add_node(NodeName.ARCH, ArchNode.call)
    graph.add_node(NodeName.ARCH_REVIEW, human_review_node)

    # 多端开发（并行）
    graph.add_node(NodeName.WEB, WebNode.call)
    graph.add_node(NodeName.H5, H5Node.call)
    graph.add_node(NodeName.MOBILE, MobileNode.call)
    graph.add_node(NodeName.API, APINode.call)
    graph.add_node(NodeName.DEV_REVIEW, human_review_node)

    # QA 相关
    graph.add_node(NodeName.QA, QANode.call)
    graph.add_node(NodeName.FIX, FixNode.call)

    # 测试相关
    graph.add_node(NodeName.TEST, TestNode.call)
    graph.add_node(NodeName.TEST_REVIEW, human_review_node)
    graph.add_node(NodeName.TEST_RUNNER, TestRunnerNode.call)
    graph.add_node(NodeName.DEBUG, DebugNode.call)

    # 部署相关
    graph.add_node(NodeName.DEPLOY, DeployNode.call)
    graph.add_node(NodeName.CHECK, CheckNode.call)

    # 归档
    graph.add_node(NodeName.STORE, StoreNode.call)

    # 设置入口点
    graph.set_entry_point(NodeName.DOC)

    # === 边定义 ===

    # PRD 流程
    graph.add_edge(NodeName.DOC, NodeName.PRD_REVIEW)

    # PRD 审核后：根据结果分流
    graph.add_conditional_edges(
        NodeName.PRD_REVIEW,
        prd_review_router,
        {
            "approved": NodeName.ARCH,          # 通过 -> 进入架构设计
            "rejected": NodeName.DOC,            # 驳回 -> 重新生成PRD
            "cancelled": END,                    # 取消 -> 结束
        }
    )

    # 架构设计流程
    graph.add_edge(NodeName.ARCH, NodeName.ARCH_REVIEW)
    graph.add_conditional_edges(
        NodeName.ARCH_REVIEW,
        arch_review_router,
        {
            "approved": NodeName.WEB,            # 通过 -> 开始多端开发
            "rejected": NodeName.ARCH,           # 驳回 -> 重新设计
            "cancelled": END,                    # 取消 -> 结束
        }
    )

    # 多端并行开发
    # 使用 Send to parallel 执行多个节点
    graph.add_conditional_edges(
        NodeName.ARCH_REVIEW,
        parallel_dev_router,
        {
            "web": NodeName.WEB,
            "h5": NodeName.H5,
            "mobile": NodeName.MOBILE,
            "api": NodeName.API,
        },
        NodeName.DEV_REVIEW,
    )

    # 开发评审
    graph.add_edge(NodeName.WEB, NodeName.DEV_REVIEW)
    graph.add_edge(NodeName.H5, NodeName.DEV_REVIEW)
    graph.add_edge(NodeName.MOBILE, NodeName.DEV_REVIEW)
    graph.add_edge(NodeName.API, NodeName.DEV_REVIEW)

    graph.add_conditional_edges(
        NodeName.DEV_REVIEW,
        dev_review_router,
        {
            "approved": NodeName.QA,             # 通过 -> 开始QA自检
            "rejected": NodeName.WEB,            # 驳回 -> 重新开发
            "cancelled": END,                    # 取消 -> 结束
        }
    )

    # QA 自检循环
    graph.add_edge(NodeName.QA, NodeName.FIX)
    graph.add_edge(NodeName.FIX, NodeName.QA)

    graph.add_conditional_edges(
        NodeName.QA,
        qa_pass_router,
        {
            "pass": NodeName.TEST,              # 通过 -> 测试用例
            "retry": NodeName.FIX,              # 失败 -> 自动修复
        }
    )

    # 测试流程
    graph.add_edge(NodeName.TEST, NodeName.TEST_REVIEW)
    graph.add_conditional_edges(
        NodeName.TEST_REVIEW,
        test_review_router,
        {
            "approved": NodeName.TEST_RUNNER,   # 通过 -> 执行测试
            "rejected": NodeName.TEST,          # 驳回 -> 重新生成
            "cancelled": END,                    # 取消 -> 结束
        }
    )

    graph.add_edge(NodeName.TEST_RUNNER, NodeName.DEBUG)
    graph.add_edge(NodeName.DEBUG, NodeName.WEB)  # 调试后回退到开发

    graph.add_conditional_edges(
        NodeName.TEST_RUNNER,
        test_pass_router,
        {
            "pass": NodeName.DEPLOY,            # 通过 -> 部署
            "fail": NodeName.DEBUG,             # 失败 -> 调试
        }
    )

    # 部署流程
    graph.add_edge(NodeName.DEPLOY, NodeName.CHECK)
    graph.add_conditional_edges(
        NodeName.CHECK,
        check_pass_router,
        {
            "pass": NodeName.STORE,             # 灰度通过 -> 归档
            "fail": NodeName.DEPLOY,            # 失败 -> 重新部署
        }
    )

    # 归档
    graph.add_edge(NodeName.STORE, END)

    return graph


# === 路由函数 ===

def prd_review_router(state: WorkflowState) -> Literal["approved", "rejected", "cancelled"]:
    """PRD 审核路由"""
    result = state.get("prd_review_result", "rejected")
    return result


def arch_review_router(state: WorkflowState) -> Literal["approved", "rejected", "cancelled"]:
    """架构审核路由"""
    result = state.get("arch_review_result", "rejected")
    return result


def dev_review_router(state: WorkflowState) -> Literal["approved", "rejected", "cancelled"]:
    """开发评审路由"""
    result = state.get("dev_review_result", "rejected")
    return result


def test_review_router(state: WorkflowState) -> Literal["approved", "rejected", "cancelled"]:
    """测试审核路由"""
    result = state.get("test_review_result", "rejected")
    return result


def qa_pass_router(state: WorkflowState) -> Literal["pass", "retry"]:
    """QA 自检结果路由"""
    qa_report = state.get("qa_report", {})
    if qa_report.get("passed"):
        return "pass"
    # 检查修复次数
    if state.get("fix_count", 0) >= state.get("max_fix_attempts", 3):
        return "pass"  # 达到最大次数，继续流程
    return "retry"


def test_pass_router(state: WorkflowState) -> Literal["pass", "fail"]:
    """测试执行结果路由"""
    test_report = state.get("test_report", {})
    if test_report.get("all_passed"):
        return "pass"
    return "fail"


def check_pass_router(state: WorkflowState) -> Literal["pass", "fail"]:
    """灰度验证结果路由"""
    if state.get("gray_release_ok"):
        return "pass"
    return "fail"


def parallel_dev_router(state: WorkflowState) -> Dict[str, str]:
    """多端并行开发路由"""
    # 返回所有需要并行执行的节点
    return {
        "web": NodeName.WEB,
        "h5": NodeName.H5,
        "mobile": NodeName.MOBILE,
        "api": NodeName.API,
    }


# === 占位节点实现 ===

async def human_review_node(state: WorkflowState, runtime: Runtime[WorkflowContext]) -> Dict[str, Any]:
    """人工审核占位节点

    实际实现中，这里应该：
    1. 通过飞书发送审核请求
    2. 等待人工审核结果
    3. 更新状态
    """
    return {}


# === 创建并编译图 ===
checkpointer = MemorySaver()
graph = create_workflow_graph().compile(
    name="enterprise_dev_workflow",
    checkpointer=checkpointer,
)
