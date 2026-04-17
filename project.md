
---

# 企业研发流程 AI 自动化 Agent 系统设计方案
## 一、项目背景与目标
### 1.1 现有流程
公司现有业务包含：**前端 Web、H5、移动端、后端服务**四类项目，需求管理、流程节点、任务审批均基于**飞书项目管理**完成，人工参与全流程执行，效率偏低、标准化不足。

### 1.2 改造目标
引入 AI Agent 自动化执行全流程节点，实现：
- AI 负责：需求分析、PRD 生成、差量分析、多端开发、代码自检、测试用例、自动化测试、部署等
- 人工只负责：各节点结果审核、驳回修正、最终上线确认
- 流程自动流转、自动重试、自动修复、自动归档
- 与飞书项目深度打通，保持现有协作习惯不变

---

## 二、AI 自动化工作流完整设计
### 2.1 流程图说明
本流程基于 LangGraph 设计，包含：子图、条件分支、并行执行、循环回流、异常终止，完全贴合真实互联网研发流程。

### 2.2 Mermaid 流程图代码
可直接粘贴至 https://mermaid.live/ 生成高清流程图：

```mermaid
flowchart TB
    %% 样式定义
    classDef startend stroke:#4f46e5,fill:#eef2ff
    classDef ai_node stroke:#0d9488,fill:#f0fdfa
    classDef human_node stroke:#f97316,fill:#fff7ed
    classDef cond_node stroke:#8b5cf6,fill:#f5f3ff
    classDef parallel stroke:#ec4899,fill:#fdf4ff
    classDef error_node stroke:#ef4444,fill:#fef2f2

    %% 1. 流程开始
    A["开始：飞书新需求创建"]:::startend
    
    %% 2. PRD生成与审核
    A --> B["PRD自动生成（Doc-Agent）"]:::ai_node
    B --> C["PRD人工审核（飞书审批）"]:::human_node
    C --> C1{"审核结果？"}:::cond_node
    C1 -->|驳回+修改意见| B
    C1 -->|通过| D{"需求类型？"}:::cond_node

    %% 3. 差量分析子图（迭代需求专用）
    subgraph Delta["差量需求分析子图（AI多Agent协作）"]
      direction TB
      D1["历史需求提取（Knowledge-Agent）"]:::ai_node
      D2["差异比对分析（Diff-Agent）"]:::ai_node
      D3["影响范围评估（Impact-Agent）"]:::ai_node
      D4["差量文档生成（Context-Agent）"]:::ai_node
      D1 --> D2 --> D3 --> D4
    end
    D -->|迭代需求| Delta
    D -->|全新需求| E

    %% 4. 架构方案与审核
    Delta --> E["研发方案自动生成（Arch-Agent）"]:::ai_node
    E --> F["方案人工审核"]:::human_node
    F --> F1{"审核结果？"}:::cond_node
    F1 -->|驳回| E
    F1 -->|通过| G

    %% 5. 多端并行开发子图
    subgraph Dev["多端并行开发子图"]
      direction TB
      G1["Web端开发（Web-Agent）"]:::parallel
      G2["H5端开发（H5-Agent）"]:::parallel
      G3["移动端开发（Mobile-Agent）"]:::parallel
      G4["后端开发（API-Agent）"]:::parallel
    end
    G --> Dev

    %% 6. 代码自检&自动修复
    Dev --> H["代码自检&规范校验（QA-Agent）"]:::ai_node
    H --> H1{"自检是否通过？"}:::cond_node
    H1 -->|不通过| H2["代码自动修复（Fix-Agent）"]:::ai_node
    H2 --> H
    H1 -->|通过| I

    %% 7. 开发结果人工评审
    I["开发成果人工评审"]:::human_node
    I --> I1{"评审结果？"}:::cond_node
    I1 -->|驳回| Dev
    I1 -->|通过| J

    %% 8. 测试用例生成&审核
    J["测试用例生成（Test-Agent）"]:::ai_node
    J --> K["用例人工审核"]:::human_node
    K --> K1{"审核结果？"}:::cond_node
    K1 -->|驳回| J
    K1 -->|通过| L

    %% 9. 自动化测试&问题定位
    L["自动化测试执行（TestRunner-Agent）"]:::ai_node
    L --> L1{"测试是否通过？"}:::cond_node
    L1 -->|不通过| L2["测试问题自动定位（Debug-Agent）"]:::ai_node
    L2 --> Dev
    L1 -->|通过| M

    %% 10. 部署&上线环节
    M["预发环境部署（Deploy-Agent）"]:::ai_node
    M --> N["灰度发布验证（Check-Agent）"]:::ai_node
    N --> O["最终上线审核&发布（人工+AI）"]:::human_node
    
    %% 11. 流程归档&结束
    O --> P["流程归档&知识库沉淀（Store-Agent）"]:::ai_node
    P --> Q["流程结束"]:::startend

    %% 异常终止分支（需求取消）
    C1 -.->|需求取消| Q
    F1 -.->|需求取消| Q
    I1 -.->|需求取消| Q
```

---

## 三、核心技术框架选型
### 3.1 核心编排框架
**唯一选择：LangGraph + LangChain**
- 原生支持子图、条件分支、并行、循环、状态持久化
- 与流程图结构 1:1 映射，开发成本最低
- 企业级 AI Agent 系统行业事实标准

### 3.2 后端服务
- FastAPI：轻量、高性能、适合 AI 服务接口化
- 提供：启动流程、审核回调、状态查询、日志查询接口

### 3.3 前端呈现方案（行业主流）
**最终选择：Web 平台（内网网页）**
- 95% 企业级 AI 协作系统均采用 Web 形态
- 可直接嵌入飞书工作台，全员无需安装软件
- 支持流程可视化、审核操作、进度查看

> 备选快速方案：Streamlit（1 小时出可演示 Web 界面）

### 3.4 集成能力
- 飞书开放平台 SDK：消息推送、审批回调、项目状态同步
- 大模型接口：GPT / 通义千问 / 文心一言等
- 代码仓库、测试平台、部署平台对接

---

## 四、系统呈现形态对比与结论
| 方案 | 适用场景 | 团队体验 | 飞书集成 | 最终选择 |
|------|----------|----------|----------|----------|
| 终端 CLI | 个人极客工具 | 极差 | 无法集成 | 否 |
| 桌面客户端 | 本地工具 | 一般 | 复杂 | 否 |
| Web 网页平台 | 企业协作、多人审核 | 优秀 | 无缝集成 | **是** |

---

## 五、落地实施步骤（第一步优先）
1. **LangGraph 流程编码**
   将 Mermaid 流程图翻译为 State、节点、条件边、子图。

2. **搭建最小 Web 演示系统**
   使用 Streamlit / FastAPI + 简单页面，实现：
   - 发起需求
   - 查看 AI 执行进度
   - 人工审核通过/驳回

3. **对接飞书**
   实现消息推送、审核卡片、状态同步。

4. **逐步接入真实开发、测试能力**
   先跑通流程，再逐步增强各 Agent 能力。

---

## 六、方案核心价值
1. 研发流程标准化、自动化，减少重复人工劳动
2. AI 负责执行，人工专注审核与决策
3. 流程可回溯、可监控、可优化
4. 完全贴合现有飞书协作体系，无额外学习成本
5. 基于 LangGraph 可无限扩展后续能力

---
