# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

这是一个基于 LangGraph 构建的**企业研发流程 AI 自动化系统**。系统通过编排多个 AI Agent 自动化执行完整的软件开发生命周期：需求分析、PRD 生成、差量分析、多端开发、代码自检、测试用例生成、自动化测试、部署。人工只需在关键节点进行审核/驳回。

完整系统设计文档见 `project.md`。

## 开发命令

```bash
# 安装依赖（包含 LangGraph CLI 用于本地开发）
pip install -e . "langgraph-cli[inmem]"

# 运行测试
make test                          # 运行所有单元测试
make test TEST_FILE=tests/unit_tests/test_configuration.py  # 运行指定文件
make test_watch                    # 测试监视模式，支持快照更新
make integration_tests             # 运行集成测试

# 代码检查与格式化
make lint                          # 运行 ruff 和 mypy
make format                        # 使用 ruff 格式化代码
make spell_check                   # 检查拼写
```

## 代码架构

```
src/
├── agent/                    # 主模块
│   ├── graph.py             # LangGraph 主图定义（工作流入口）
│   ├── state.py             # WorkflowState 和 WorkflowContext 类型定义
│   └── __init__.py
├── nodes/                    # 所有工作流节点实现
│   ├── base.py              # 节点基类 BaseNode
│   ├── prd/                 # PRD 生成节点 (DocNode) - 子图
│   │   └── doc.py           # DocNode 主类
│   ├── delta/               # 差量分析子图节点
│   │   ├── knowledge.py     # KnowledgeNode - 历史需求提取
│   │   ├── diff.py          # DiffNode - 差异比对
│   │   ├── impact.py        # ImpactNode - 影响评估
│   │   └── context.py        # ContextNode - 差量文档生成
│   ├── arch/                # 架构设计节点 (ArchNode)
│   ├── dev/                 # 多端开发节点
│   │   ├── web.py           # WebNode
│   │   ├── h5.py            # H5Node
│   │   ├── mobile.py        # MobileNode
│   │   └── api.py           # APINode
│   ├── qa/                  # QA 审核节点
│   │   ├── qa.py            # QANode - 代码自检
│   │   └── fix.py           # FixNode - 自动修复
│   ├── test/                # 测试节点
│   │   ├── test.py          # TestNode - 用例生成
│   │   ├── test_runner.py   # TestRunnerNode - 测试执行
│   │   └── debug.py         # DebugNode - 问题定位
│   ├── deploy/              # 部署节点
│   │   ├── deploy.py        # DeployNode
│   │   └── check.py         # CheckNode - 灰度验证
│   └── archive/              # 归档节点
│       └── store.py          # StoreNode
├── graphs/                  # 图定义模块
│   └── subgraphs/           # 子图定义
│       ├── doc_subgraph.py  # DocNode 子图（PRD 生成流程）
│       └── doc_graph.py     # DocNode 子图状态定义
├── agents/                  # Agent 实现模块
│   ├── doc_agent.py         # DocAgent - 需求生成 Agent
│   └── review_agent.py      # ReviewAgent - 专家审核 Agent
├── tools/                   # 工具函数
│   ├── file_scanner.py      # 文件扫描工具（支持 PDF/Word/图片/Markdown）
│   └── file_reader.py       # 文件内容提取工具
├── state/                   # 状态和上下文模块（可导出类型）
├── prompts/                 # 提示词模板
└── models/                  # 模型配置
```

### DocNode 子图架构

DocNode 是一个完整的子图，包含以下流程：

```
scan_files → extract_content → generate_prd → check_user_input
                                                      ↓
                                          [需要用户介入] → request_user_input
                                                      ↓
                                          [不需要用户介入] → review_prd
                                                                 ↓
                                              [approved] → output_prd
                                              [rejected] → generate_prd
```

**子图节点：**
- `scan_files`: 扫描 `doc/requestion` 目录下的文件
- `extract_content`: 提取文件内容（支持 PDF、Word、图片、Markdown）
- `generate_prd`: DocAgent 根据内容生成 PRD 草稿，同时检测逻辑完整性
- `check_user_input`: 检测是否需要用户介入补充内容
- `request_user_input`: 等待用户补充内容（支持文本输入或文件）
- `review_prd`: ReviewAgent 审核 PRD（评分机制，≥90分通过）
- `output_prd`: 将最终 PRD 输出到 `doc/output` 目录

**Agent 说明：**
- DocAgent：产品经理角色，生成 PRD 草稿，同时检测逻辑不完整或冲突
- ReviewAgent：专家审核角色，评分并给出修改意见（超过100字的需求至少审核一次）

**用户介入机制：**
- DocAgent 在生成 PRD 过程中，如果发现逻辑不完整或冲突，会在 PRD 末尾标注
- 系统会提示用户需要补充的内容
- 用户可以通过文本直接输入或提供补充文件
- 尽可能一次性列出所有需要补充的点，减少打断次数

**文件路径：**
- 输入目录：`D:/pyProject/bruce_project_flow/doc/requestion`
- 输出目录：`D:/pyProject/bruce_project_flow/doc/output`

### 核心文件说明

- **`src/agent/graph.py`**: 主工作流图定义，包含所有节点定义、边连接、路由函数。`langgraph.json` 引用此文件的 `graph` 对象。
- **`src/agent/state.py`**: `WorkflowState`（状态）和 `WorkflowContext`（上下文）类型定义。
- **`src/nodes/base.py`**: `BaseNode` 抽象基类，所有节点应继承。
- **`langgraph.json`**: LangGraph CLI 配置。

### 节点开发规范

每个节点实现为一个类，提供静态方法 `call`:

```python
class MyNode:
    @staticmethod
    async def call(state: WorkflowState, runtime: Runtime[WorkflowContext]) -> Dict[str, Any]:
        # 处理逻辑
        return {"key": "value"}
```

## 运行服务

```bash
langgraph dev   # 启动 LangGraph Server，支持热重载
```

启动后，访问终端中显示的 LangGraph Studio URL，可视化调试图执行过程。

## 主要依赖

- `langgraph>=1.0.0` - 工作流编排
- `python-dotenv>=1.0.1` - 环境变量管理
- `langchain-openai>=0.0.5` - 大模型调用
- `pypdf>=4.0.0` - PDF 文件处理
- `python-docx>=1.0.0` - Word 文件处理
- `mypy>=1.11.1`, `ruff>=0.6.1` - 开发代码检查
