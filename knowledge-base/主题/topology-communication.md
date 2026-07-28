---
type: theme
tags:
  - theme
  - topology-communication
---

# 主题：动态拓扑与低熵通信 (topology-communication)

**赛题核心支柱②**。任务自适应生成/剪枝多 agent 通信图，抑制冗余与噪声级联。这是赛题最大的创新空间。

## 方法谱系（按生成范式）
**A. 图优化/学习**
- [[2402.16823 GPTSwarm]]：agent=图、自动优化节点 prompt 与边连通性。
- [[2410.11782 G-Designer]]：变分图自编码器解码任务自适应拓扑，token 降 95%、抗对抗。
- [[2506.02951 Adaptive Graph Pruning]]：hard(选 agent 数)+soft(选边)联合剪枝，token 降 90%+。
- [[2410.02506 AgentPrune]]：时空消息图一次性剪枝，去冗余/恶意，token 降 28-72%。

**B. 搜索/架构搜索**
- [[2310.02170 DyLAN]]：Agent Importance Score 选团队 + T-FFN 动态结构。
- [[2410.10762 AFlow]]：workflow=代码图，MCTS 自动生成。
- [[2502.04180 MaAS Agentic Supernet]]：从 supernet 按查询采样架构，6-45% 成本。

**C. 生成式（从零生成图）**
- [[2507.18224 ARG-Designer]]：自回归从零生成 agent 组成+通信链。
- [[2510.07799 GTD Graph Diffusion Topology]]：图扩散+多目标(性能/成本/鲁棒)逐步引导。

**D. 去中心化/路由**
- [[2606.10662 DeLM Decentralized MAS]]：共享已验证上下文+任务队列，去中心化。
- [[2606.22902 Agent-as-a-Router]]：C-A-F 循环 agentic 路由，regret 评测。

## 综合洞察
- **共识**：静态全连接/手工拓扑浪费 token 且不适配任务难度；**任务自适应稀疏图**是统一方向。
- **两难**：既要低熵（稀疏、剪枝），又要保足够连通度以容错（[[2606.15024 Resilient Consensus in Agentic AI]]：N≥3B+1）。
- **生成式 > 模板修改**：ARG-Designer/GTD 从零生成，突破"模板图修改"的冗余与僵化。
- **多目标**：GTD 同时优化性能/成本/鲁棒——赛题多打分点应纳入同一目标函数。
- **可量化**：AgentPrune/G-Designer 的 token 降幅可作赛题"降噪创新"的可演示证据。

## 与赛题关联
> 支柱：② 动态拓扑低熵通信（核心）/ ④ 鲁棒容错
- 动态拓扑算法可选 G-Designer(图自编码) / AGP(双剪枝) / ARG-Designer(自回归) / GTD(扩散多目标) 之一为底座，扩展为以"低熵/低 token"为优化目标。
- 消息出口做 AgentPrune 式剪枝/结构化过滤；agent 间强制 typed schema 消息。
- 拓扑须保连通度以容 B 个失效节点（拜占庭容错）。

## 全部笔记
[[2310.02170 DyLAN]] · [[2402.16823 GPTSwarm]] · [[2410.02506 AgentPrune]] · [[2410.10762 AFlow]] · [[2410.11782 G-Designer]] · [[2502.04180 MaAS Agentic Supernet]] · [[2506.02951 Adaptive Graph Pruning]] · [[2507.18224 ARG-Designer]] · [[2510.07799 GTD Graph Diffusion Topology]] · [[2606.10662 DeLM Decentralized MAS]] · [[2606.22902 Agent-as-a-Router]]
