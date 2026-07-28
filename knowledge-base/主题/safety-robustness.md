---
type: theme
tags:
  - theme
  - safety-robustness
---

# 主题：安全与鲁棒性 (safety-robustness)

**赛题支柱④**。拜占庭容错、隐性失效诊断、可观测——"接受异常注入、节点失效、需求变更"。

## 核心文献
- [[2606.15024 Resilient Consensus in Agentic AI]]：LLM agent 共识建模为拜占庭博弈；prompt agent 在安全区内仍失败；经典 MSR 滤波恢复共识；拓扑连通度决定容错上限（N≥3B+1，B<κ/2）。
- [[2606.22936 Premature Commitment in LLM Agents]]：agent 过早锁定解读的隐性失败；隐状态跨运行收敛可诊断，运行时监测 AUROC 0.97。
- [[2606.22953 Plans Dont Persist]]：上下文管理承重，计划驱逐 -34.7pp（见 [[memory-longcontext]]）。

## 关联方法（容错落在其他主题但服务本支柱）
- [[2303.11366 Reflexion]]：失败→语言反思→重试（verbal RL）。
- [[2310.04406 LATS Language Agent Tree Search]]：MCTS 回溯重选。
- [[2410.02506 AgentPrune]]：抗 agent 对抗攻击 +3.5-10.8%。
- [[2410.11782 G-Designer]]：抗对抗仅 0.3% drop。
- [[2402.14034 AgentScope]]：容错防级联一等公民。
- [[2606.04990 Agent Traces to Trust Survey]]：provenance 图支撑失败定位与恢复。

## 综合洞察
- **拓扑连通度 = 容错上限**：动态拓扑不仅要低熵，还要保足够连通度以容 B 个失效/对抗节点。
- **隐性失效最危险**：过早承诺、计划驱逐都不崩溃却悄悄降质——需运行时监测（隐状态/provenance）。
- **容错需分层**：瞬时(本地重试)→语义(Reflexion)→能力缺口(重规划)→环境态(重感知)→需求变更(上抛)→熔断。
- **经典分布式理论可迁移**：MSR 滤波、拜占庭共识为赛题提供形式化容错框架。

## 与赛题关联
> 支柱：④ 鲁棒容错（核心）/ ② 拓扑
- 分层异常处理：L0 瞬时(退避)/L1 语义(Reflexion)/L2 能力(重规划)/L3 环境(重感知)/L4 需求变更(上抛)+熔断。
- 拓扑设计纳入连通度约束以容节点失效；消息层用 AgentPrune 抗对抗。
- 日志用 provenance 图（[[2606.04990 Agent Traces to Trust Survey]]）支撑失败定位与恢复，并可演示"推理轨迹"。
- 演示：现场注入 L0-L4 故障，展示系统自愈——强打分点。

## 全部笔记
[[2606.15024 Resilient Consensus in Agentic AI]] · [[2606.22936 Premature Commitment in LLM Agents]] ·（关联 [[2303.11366 Reflexion]] [[2310.04406 LATS Language Agent Tree Search]] [[2410.02506 AgentPrune]] [[2410.11782 G-Designer]] [[2402.14034 AgentScope]] [[2606.04990 Agent Traces to Trust Survey]] [[2606.22953 Plans Dont Persist]]）
