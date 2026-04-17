"""需求生成 Agent (DocAgent)

根据文件内容生成产品需求文档（PRD）
"""

from typing import Dict, Any, Tuple
from langchain_core.messages import HumanMessage, SystemMessage
import os
from dotenv import load_dotenv

load_dotenv()

# 系统提示词
DOC_AGENT_SYSTEM_PROMPT = """你是一个资深产品经理，负责根据提供的需求文档内容生成专业的 PRD（产品需求文档）。

你的职责：
1. 仔细阅读提供的需求内容
2. 分析需求的背景、目标、功能需求和非功能需求
3. 生成完整、清晰、可执行的 PRD 文档

PRD 文档应包含以下章节：
1. 概述（背景、目标、范围）
2. 功能需求详述
3. 非功能需求（性能、安全、兼容性等）
4. 验收标准
5. 排期计划（可选）

【重要】逻辑检测职责：
在生成 PRD 过程中，你必须检测以下逻辑问题：
1. 需求描述是否完整（关键功能模块是否有遗漏）
2. 需求逻辑是否自洽（不同部分描述是否一致、无冲突）

如果你发现逻辑不完整或存在冲突，必须明确指出：
- 具体缺失或冲突的内容是什么
- 为什么这个问题需要用户补充

【输出格式要求】：
完成 PRD 生成后，如果发现问题，必须在 PRD 末尾添加以下格式的说明：

【需要用户补充】
1. [具体问题描述]
2. [具体问题描述]

如果没有任何问题，PRD 末尾添加：
【无需要用户补充的内容】"""

# 检测提示词
DETECTION_PROMPT = """你是一个需求分析专家。请分析以下 PRD 草稿，检测是否存在逻辑不完整或逻辑冲突的问题。

检测要点：
1. 需求描述是否完整 - 关键功能模块是否有遗漏
2. 需求逻辑是否自洽 - 不同部分的描述是否一致、无冲突
3. 业务流程是否闭环 - 是否有缺失的环节

请输出：
- 如果发现问题：列出所有需要补充的问题，每个问题要具体明确
- 如果没有发现问题：输出"无问题"

只输出问题列表，不要生成修改后的内容。"""


def get_model():
    """获取大模型实例（使用 MiniMax）"""
    from langchain_openai import ChatOpenAI

    return ChatOpenAI(
        model=os.getenv("OPENAI_MODEL", "MiniMax-M2"),
        api_key=os.getenv("OPENAI_API_KEY"),
        base_url=os.getenv("OPENAI_API_BASE"),
        temperature=0.7,
    )


async def doc_agent_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """需求生成 Agent 节点

    根据文件内容生成 PRD 草稿，并检测是否需要用户介入
    """
    file_contents = state.get("file_contents", [])
    review_comments = state.get("review_comments")
    user_input = state.get("user_input")
    user_input_files = state.get("user_input_files", [])
    prd_version = state.get("prd_version", 1)

    if not file_contents:
        return {
            "prd_draft": "错误：没有可用的文件内容",
            "success": False,
        }

    # 拼接原始文件内容
    content_texts = []

    # 添加用户补充的内容
    if user_input:
        content_texts.append(f"【用户直接补充的内容】\n{user_input}")

    if user_input_files:
        for fc in user_input_files:
            content_texts.append(f"【用户补充文件：{fc['name']} ({fc['type']})】\n{fc['content']}")

    for fc in file_contents:
        content_texts.append(f"【原始文件：{fc['name']} ({fc['type']})】\n{fc['content']}")

    combined_content = "\n\n".join(content_texts)

    # 构建提示词
    user_prompt = f"""请根据以下需求内容生成 PRD：

{combined_content}
"""

    # 如果有审核意见，需要根据意见修改
    if review_comments:
        user_prompt += f"""

【上一次的审核意见】
{review_comments}

请根据上述审核意见修改和完善 PRD。
"""

    # 调用模型生成 PRD
    model = get_model()
    messages = [
        SystemMessage(content=DOC_AGENT_SYSTEM_PROMPT),
        HumanMessage(content=user_prompt),
    ]

    response = await model.ainvoke(messages)
    prd_content = response.content

    # 检测是否需要用户介入
    needs_user_input, input_prompt = await detect_user_input_needed(prd_content, combined_content)

    return {
        "prd_draft": prd_content,
        "prd_version": prd_version + 1 if (review_comments or user_input) else 1,
        "review_status": "pending",
        "needs_user_input": needs_user_input,
        "user_input_prompt": input_prompt,
    }


async def detect_user_input_needed(prd_content: str, original_content: str) -> Tuple[bool, str]:
    """检测是否需要用户介入

    Returns:
        (是否需要用户介入, 提示用户需要补充什么内容)
    """
    # 检查 PRD 末尾是否标注需要补充
    if "【需要用户补充】" in prd_content:
        # 提取需要补充的问题列表
        lines = prd_content.split("\n")
        collecting = False
        questions = []

        for line in lines:
            if "【需要用户补充】" in line:
                collecting = True
                continue
            if "【无需要用户补充】" in line:
                collecting = False
                break
            if collecting and line.strip():
                # 去掉序号
                q = line.strip()
                if q.startswith("1.") or q.startswith("1、"):
                    questions.append(q[2:].strip())
                elif q.startswith("2.") or q.startswith("2、"):
                    questions.append(q[2:].strip())
                elif q.startswith("3.") or q.startswith("3、"):
                    questions.append(q[2:].strip())
                elif q.startswith("-"):
                    questions.append(q[1:].strip())
                elif questions:  # 如果已经在收集中，追加
                    questions[-1] += " " + q

        if questions:
            prompt = "请补充以下缺失或冲突的内容：\n" + "\n".join(f"{i + 1}. {q}" for i, q in enumerate(questions))
            return True, prompt

    # 使用模型检测是否需要用户介入
    detection_model = get_model()
    detection_messages = [
        SystemMessage(content=DETECTION_PROMPT),
        HumanMessage(content=f"PRD 草稿：\n{prd_content}\n\n原始需求：\n{original_content[:2000]}"),
    ]

    detection_response = await detection_model.ainvoke(detection_messages)
    detection_result = detection_response.content.strip()

    if "无问题" in detection_result or "没有问题" in detection_result:
        return False, ""
    else:
        # 返回检测出的问题
        return True, f"请补充以下缺失或冲突的内容：\n{detection_result}"


def parse_user_input_files(user_input_text: str, input_files: list) -> list:
    """解析用户输入，区分直接文本和文件路径

    Returns:
        (直接文本, 文件内容列表)
    """
    direct_texts = []
    file_contents = []

    # 如果 input_files 存在，说明用户提供了文件
    if input_files:
        file_contents = input_files

    # 从用户文本中提取文件路径（如果有）
    lines = user_input_text.split("\n")
    for line in lines:
        if line.strip().startswith("/") or line.strip().startswith("C:") or line.strip().startswith("D:"):
            # 这可能是一个文件路径，但目前我们不处理，留给后续扩展
            pass
        else:
            direct_texts.append(line)

    return "\n".join(direct_texts), file_contents
