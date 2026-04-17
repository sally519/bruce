"""专家审核 Agent (ReviewAgent)

审核 PRD 草稿，决定是否通过或需要修改
"""

from typing import Dict, Any, Tuple
import os
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage

load_dotenv()


# 系统提示词
REVIEW_AGENT_SYSTEM_PROMPT = """你是一个资深产品专家和评审委员会成员，负责审核产品需求文档（PRD）的质量。

你的评审标准：
1. 完整性：PRD 是否包含所有必要章节
2. 清晰度：描述是否清晰、无歧义
3. 可行性：需求是否技术可行
4. 可测试性：是否有明确的验收标准
5. 一致性：各章节描述是否一致

评分规则（0-100分）：
- 90-100：优秀，可以直接通过
- 70-89：良好，有小问题需要修改
- 60-69：一般，有较大问题需要修改
- 60以下：不合格，需要重大修改

重要规则：
- 对于超过 100 字的需求描述，必须至少提出一次具体的修改建议
- 如果评分低于 90，必须给出具体的修改意见
- 评分达到 90 及以上才能通过审核

输出格式：
请严格按以下格式输出评审结果：

## 评审结论
[通过/需修改/不通过]

## 评分
[0-100]

## 评审意见
[具体的问题描述和修改建议，如果没有问题则写"无"]
"""


# 评分阈值
PASSING_SCORE = 90
MIN_REVIEW_ITERATIONS = 1  # 至少审核一次


def get_model():
    """获取大模型实例（使用 MiniMax）"""
    from langchain_openai import ChatOpenAI

    return ChatOpenAI(
        model=os.getenv("OPENAI_MODEL", "MiniMax-M2"),
        api_key=os.getenv("OPENAI_API_KEY"),
        base_url=os.getenv("OPENAI_API_BASE"),
        temperature=0.3,  # 审核用较低温度
    )


def parse_review_response(response_content: str) -> Tuple[str, float, str]:
    """解析审核响应

    Returns:
        (结论, 评分, 评审意见)
    """
    conclusion = "需修改"
    score = 0.0
    comments = ""

    lines = response_content.split("\n")
    current_section = ""

    for line in lines:
        line = line.strip()
        if "评审结论" in line or "结论" in line:
            current_section = "conclusion"
            continue
        elif "评分" in line:
            current_section = "score"
            continue
        elif "评审意见" in line or "意见" in line:
            current_section = "comments"
            continue

        if current_section == "conclusion" and line:
            if "通过" in line:
                conclusion = "通过"
            elif "不通过" in line:
                conclusion = "不通过"
            else:
                conclusion = "需修改"

        elif current_section == "score" and line:
            # 提取数字
            import re
            numbers = re.findall(r'\d+\.?\d*', line)
            if numbers:
                score = float(numbers[0])

        elif current_section == "comments" and line:
            comments += line + "\n"

    return conclusion, score, comments.strip()


async def review_agent_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """专家审核 Agent 节点

    审核 PRD 草稿并给出结论
    """
    prd_draft = state.get("prd_draft", "")
    review_iterations = state.get("review_iterations", 0)
    file_contents = state.get("file_contents", [])

    if not prd_draft:
        return {
            "review_status": "rejected",
            "review_comments": "PRD 草稿为空",
            "review_score": 0.0,
            "success": False,
        }

    # 提取原始需求长度（判断是否超过 100 字）
    original_requirement_length = 0
    for fc in file_contents:
        original_requirement_length += len(fc.get("content", ""))

    # 构建审核提示词
    user_prompt = f"""请审核以下 PRD 草稿：

{prd_draft}

基础信息：
- 原始需求总字数：{original_requirement_length} 字
- 当前审核轮次：第 {review_iterations + 1} 轮
"""

    # 调用模型
    model = get_model()
    messages = [
        SystemMessage(content=REVIEW_AGENT_SYSTEM_PROMPT),
        HumanMessage(content=user_prompt),
    ]

    response = await model.ainvoke(messages)
    review_content = response.content

    # 解析审核结果
    conclusion, score, comments = parse_review_response(review_content)

    # 判断是否通过
    # 规则：评分 >= 90 且（超过100字的需求至少审核过一次 或 评分>=95）
    pass_required = score >= PASSING_SCORE
    min_iteration_required = review_iterations >= MIN_REVIEW_ITERATIONS

    if pass_required and (original_requirement_length <= 100 or min_iteration_required):
        final_status = "approved"
        success = True
        final_prd = prd_draft
    else:
        final_status = "rejected"
        success = False
        final_prd = None

    return {
        "review_status": final_status,
        "review_comments": comments if final_status == "rejected" else "审核通过",
        "review_score": score,
        "review_iterations": review_iterations + 1,
        "final_prd": final_prd,
        "success": success,
    }
