"""PRD 生成子图

工作流程：
1. 扫描输入目录，获取文件列表
2. 提取文件内容
3. DocAgent 生成 PRD 草稿
4. 检测是否需要用户介入
   - 需要 → 使用 interrupt 等待用户在 LangSmith Studio 上输入 → 回到步骤3
   - 不需要 → ReviewAgent 审核 PRD
5. 审核通过则输出最终 PRD
"""

import asyncio
from typing import Dict, Any, Literal
from langgraph.graph import StateGraph, END
from langgraph.types import interrupt
from pathlib import Path

from graphs.subgraphs.doc_graph import DocSubGraphState, ReviewStatus
from agents.doc_agent import doc_agent_node
from agents.review_agent import review_agent_node
from tools.file_scanner import scan_files
from tools.file_reader import extract_file_content


# 节点名称
class DocNodeName:
    SCAN_FILES = "scan_files"
    EXTRACT_CONTENT = "extract_content"
    GENERATE_PRD = "generate_prd"
    CHECK_USER_INPUT = "check_user_input"
    REQUEST_USER_INPUT = "request_user_input"
    REVIEW_PRD = "review_prd"
    OUTPUT_PRD = "output_prd"


def create_doc_subgraph() -> StateGraph:
    """创建 PRD 生成子图"""
    graph = StateGraph(DocSubGraphState)

    # 添加节点
    graph.add_node(DocNodeName.SCAN_FILES, scan_files_node)
    graph.add_node(DocNodeName.EXTRACT_CONTENT, extract_content_node)
    graph.add_node(DocNodeName.GENERATE_PRD, generate_prd_node)
    graph.add_node(DocNodeName.CHECK_USER_INPUT, check_user_input_node)
    graph.add_node(DocNodeName.REQUEST_USER_INPUT, request_user_input_node)
    graph.add_node(DocNodeName.REVIEW_PRD, review_prd_node)
    graph.add_node(DocNodeName.OUTPUT_PRD, output_prd_node)

    # 设置入口
    graph.set_entry_point(DocNodeName.SCAN_FILES)

    # 主流程边
    graph.add_edge(DocNodeName.SCAN_FILES, DocNodeName.EXTRACT_CONTENT)
    graph.add_edge(DocNodeName.EXTRACT_CONTENT, DocNodeName.GENERATE_PRD)
    graph.add_edge(DocNodeName.GENERATE_PRD, DocNodeName.CHECK_USER_INPUT)

    # 用户介入分支
    graph.add_conditional_edges(
        DocNodeName.CHECK_USER_INPUT,
        user_input_decision,
        {
            "needs_input": DocNodeName.REQUEST_USER_INPUT,
            "no_input": DocNodeName.REVIEW_PRD,
        }
    )

    # 用户输入后回到生成 PRD
    graph.add_edge(DocNodeName.REQUEST_USER_INPUT, DocNodeName.GENERATE_PRD)

    # 审核分支
    graph.add_conditional_edges(
        DocNodeName.REVIEW_PRD,
        review_decision,
        {
            "approved": DocNodeName.OUTPUT_PRD,
            "rejected": DocNodeName.GENERATE_PRD,
        }
    )

    graph.add_edge(DocNodeName.OUTPUT_PRD, END)

    return graph


# === 节点实现 ===

async def scan_files_node(state: DocSubGraphState) -> Dict[str, Any]:
    """扫描文件节点"""
    input_dir = state.get("input_directory", "")

    # 使用 to_thread 处理阻塞的文件扫描操作
    files = await asyncio.to_thread(scan_files, input_dir)

    return {
        "files": files,
    }


async def extract_content_node(state: DocSubGraphState) -> Dict[str, Any]:
    """提取文件内容节点"""
    files = state.get("files", [])

    async def extract_one(file_info: Dict[str, Any]) -> Dict[str, Any]:
        try:
            content = await asyncio.to_thread(extract_file_content, file_info["path"])
            return {
                **file_info,
                "content": content["content"],
            }
        except Exception as e:
            return {
                **file_info,
                "content": f"[无法提取内容: {str(e)}]",
            }

    # 并行提取所有文件内容
    file_contents = await asyncio.gather(*[extract_one(f) for f in files])

    return {
        "file_contents": list(file_contents),
    }


async def generate_prd_node(state: DocSubGraphState) -> Dict[str, Any]:
    """生成 PRD 节点（调用 DocAgent）"""
    return await doc_agent_node(state)


async def check_user_input_node(state: DocSubGraphState) -> Dict[str, Any]:
    """检测是否需要用户介入节点

    DocAgent 已经完成了检测，在这里只需要决定下一步
    """
    needs_user_input = state.get("needs_user_input", False)

    return {
        "_continue": needs_user_input,  # 标记是否需要继续用户介入流程
    }


def user_input_decision(state: DocSubGraphState) -> Literal["needs_input", "no_input"]:
    """用户介入决策路由"""
    needs_user_input = state.get("needs_user_input", False)

    if needs_user_input:
        return "needs_input"
    return "no_input"


async def request_user_input_node(state: DocSubGraphState) -> Dict[str, Any]:
    """请求用户介入节点

    使用 interrupt 暂停执行，等待用户在 LangSmith Studio 上输入
    """
    user_input_prompt = state.get("user_input_prompt", "请补充以下内容：")

    # 增加请求计数
    current_count = state.get("input_request_count", 0)

    # 使用 interrupt 暂停，等待用户在 Studio 上输入
    # 用户输入的值会作为 user_input 返回
    user_response = interrupt({
        "prompt": user_input_prompt,
        "message": "需要用户补充内容，请在下方输入补充内容或上传文件路径"
    })

    # 从 interrupt 返回的值中获取用户输入
    user_input_text = user_response.get("user_input", "") if isinstance(user_response, dict) else str(user_response)

    return {
        "user_input_prompt": user_input_prompt,
        "input_request_count": current_count + 1,
        "user_input": user_input_text,
        "user_input_files": user_response.get("user_input_files", []) if isinstance(user_response, dict) else [],
    }


async def review_prd_node(state: DocSubGraphState) -> Dict[str, Any]:
    """审核 PRD 节点（调用 ReviewAgent）"""
    return await review_agent_node(state)


async def output_prd_node(state: DocSubGraphState) -> Dict[str, Any]:
    """输出 PRD 节点"""
    # 输出目录为 doc/result
    output_dir = Path("D:/pyProject/bruce_project_flow/doc/result")

    output_path = str(output_dir / "PRD_最终版.md")
    final_prd = state.get("final_prd", "")

    # 使用 asyncio.to_thread 处理阻塞的文件操作
    async def write_file():
        output_dir.mkdir(exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(final_prd)

    await asyncio.to_thread(write_file)

    return {
        "output_path": output_path,
    }


def review_decision(state: DocSubGraphState) -> Literal["approved", "rejected"]:
    """审核决策路由"""
    review_status = state.get("review_status", "rejected")
    return review_status


# === 编译子图 ===
doc_subgraph = create_doc_subgraph().compile(name="doc_subgraph")
