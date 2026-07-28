---
type: theme
tags:
  - theme
  - software-engineering
---

# 主题：软件工程智能体 (software-engineering)

赛题候选演示场景之一：系统级软件工程自动化。跨文件长上下文、执行式验证、真实 issue。

## 核心文献
- [[2310.06770 SWE-bench]]：2294 真实 GitHub issue + 单元测试验证，跨文件长上下文，当时最强 1.96%。
- [[2405.15793 SWE-agent]]：Agent-Computer Interface(ACI)，少量简洁 LM-friendly 动作+明确反馈，SWE-bench 12.5%。
- [[2407.01489 Agentless]]：无 agent 三阶段(定位→修复→验证)，32% / $0.70，警示"并非都要复杂 agent"。
- [[2307.07924 ChatDev]]：chat chain + 去幻觉通信，多 agent 软件开发。
- [[2308.00352 MetaGPT]]：SOP + 结构化交接，协作 SE。
- [[2407.16741 OpenHands]]：事件流+Docker 沙箱+CodeAct，通用 SE 平台。
- [[2606.10662 DeLM Decentralized MAS]]：去中心化+共享上下文，SWE-bench Verified 最佳。

## 综合洞察
- **接口设计 > 模型能力**：SWE-agent 证明 ACI（不改权重）即可大幅提升——赛题执行引擎工具接口的核心依据。
- **执行式验证**：SWE-bench 用单元测试判功能正确性，非字符串匹配——赛题评测方法学。
- **复杂度自适应**：Agentless 警示简单子任务用轻量流水线，复杂子任务才用多 agent（呼应 MaAS/G-Designer 的难度自适应）。
- **长程跨文件**是 SWE 的天然长程特征，契合赛题"数千步复杂任务"。

## 与赛题关联
> 支柱：鲁棒容错 / 低熵通信 / 多任务演示
- 场景 A 的执行层基线：SWE-agent ACI + OpenHands 沙箱 + Reflexion 重试。
- 可选 SWE-bench 子集（如 SWE-bench Lite/Verified）作演示与评测，体现长程+功能验证。
- ChatDev/MetaGPT 提供多 agent SE 的组织范式（但拓扑需动态化）。

## 全部笔记
[[2307.07924 ChatDev]] · [[2405.15793 SWE-agent]] · [[2407.01489 Agentless]] ·（关联 [[2310.06770 SWE-bench]] [[2308.00352 MetaGPT]] [[2407.16741 OpenHands]] [[2606.10662 DeLM Decentralized MAS]]）
