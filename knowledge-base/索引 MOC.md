---
type: moc
tags:
  - index
  - moc
---

# 索引 MOC · 群体智能文献库

> 服务于赛题 **XH-202631：面向超长程复杂任务的动态异构群体智能架构与深度协同推理技术**。
> 本库汇总 81 篇核心文献，按主题聚类，并映射到赛题四大支柱。每篇笔记含：一句话总结、问题与动机、核心方法、关键贡献、实验数据、局限、**与赛题关联**、相关笔记。

## 赛题四大支柱 ↔ 文献映射

| 支柱 | 核心文献 | 主题笔记 |
|---|---|---|
| **① 长程上下文连续性与记忆保持** | [[2307.03172 Lost in the Middle]] · [[2310.08560 MemGPT]] · [[2310.06839 LongLLMLingua]] · [[2504.19413 Mem0]] · [[2507.03724 MemOS]] · [[2601.01885 Agentic Memory]] · [[2606.22953 Plans Dont Persist]] · [[2304.03442 Generative Agents]] · [[2606.22877 DynamicMem]] | [[memory-longcontext]] |
| **② 动态异构拓扑与低熵通信** | [[2410.11782 G-Designer]] · [[2402.16823 GPTSwarm]] · [[2502.04180 MaAS Agentic Supernet]] · [[2506.02951 Adaptive Graph Pruning]] · [[2507.18224 ARG-Designer]] · [[2510.07799 GTD Graph Diffusion Topology]] · [[2410.02506 AgentPrune]] · [[2310.02170 DyLAN]] · [[2606.10662 DeLM Decentralized MAS]] · [[2502.14321 Communication-Centric Survey]] · [[2606.19135 Agent Communication Protocols Taxonomy]] | [[topology-communication]] |
| **③ 端-边-云异构资源自适应调度** | [[2405.14371 EdgeShard]] · [[2209.01188 PETALS]] · [[2311.18677 Splitwise]] · [[2401.09670 DistServe]] · [[2401.14351 ServerlessLLM]] · [[2606.15210 QLMIO Multimodal LLM Offloading]] · [[2606.17489 Online LLM Selection Bandits]] · [[2404.14294 Survey Efficient LLM Inference]] | [[inference-serving]] |
| **④ 鲁棒容错 / 自主纠错** | [[2606.15024 Resilient Consensus in Agentic AI]] · [[2303.11366 Reflexion]] · [[2310.04406 LATS Language Agent Tree Search]] · [[2410.02506 AgentPrune]] · [[2606.22936 Premature Commitment in LLM Agents]] · [[2606.04990 Agent Traces to Trust Survey]] · [[2402.14034 AgentScope]] | [[safety-robustness]] |

## 按主题浏览

### 🧠 推理范式 reasoning (8)
单体 LLM 的"慢思考"骨架：从线性链到树/图/MCTS 搜索。→ [[reasoning]]
- [[2201.11903 Chain-of-Thought Prompting]] · [[2203.11171 Self-Consistency]] · [[2205.10625 Least-to-Most Prompting]] · [[2211.10435 PAL Program-aided Language Models]] · [[2211.12588 Program of Thoughts]] · [[2305.10601 Tree of Thoughts]] · [[2308.09687 Graph of Thoughts]] · [[2310.04406 LATS Language Agent Tree Search]]

### 🔧 工具调用与行动 tool-use (6)
agent 接入外部工具/环境的范式。→ [[tool-use]]
- [[2205.00445 MRKL Systems]] · [[2210.03629 ReAct]] · [[2302.04761 Toolformer]] · [[2303.11366 Reflexion]] · [[2305.15334 Gorilla]] · [[2307.16789 ToolLLM]]

### 🏛️ 智能体框架与平台 agent-framework (12)
多 agent 编排与通用 agent 平台。→ [[agent-framework]]
- [[2303.17580 HuggingGPT]] · [[2303.17760 CAMEL]] · [[2304.03442 Generative Agents]] · [[2305.16291 VOYAGER]] · [[2308.00352 MetaGPT]] · [[2308.08155 AutoGen]] · [[2308.10848 AgentVerse]] · [[2310.10634 OpenAgents]] · [[2402.14034 AgentScope]] · [[2407.16741 OpenHands]] · [[2411.04468 Magentic-One]] · [[2501.04227 Agent Laboratory]]

### 🕸️ 动态拓扑与低熵通信 topology-communication (11)
**赛题核心**：任务自适应生成/剪枝通信图。→ [[topology-communication]]
- [[2310.02170 DyLAN]] · [[2402.16823 GPTSwarm]] · [[2410.02506 AgentPrune]] · [[2410.10762 AFlow]] · [[2410.11782 G-Designer]] · [[2502.04180 MaAS Agentic Supernet]] · [[2506.02951 Adaptive Graph Pruning]] · [[2507.18224 ARG-Designer]] · [[2510.07799 GTD Graph Diffusion Topology]] · [[2606.10662 DeLM Decentralized MAS]] · [[2606.22902 Agent-as-a-Router]]

### 💾 记忆与长上下文 memory-longcontext (11)
分布式记忆、压缩唤醒、抗遗忘。→ [[memory-longcontext]]
- [[2305.10250 MemoryBank]] · [[2307.03172 Lost in the Middle]] · [[2310.05736 LLMLingua]] · [[2310.06839 LongLLMLingua]] · [[2310.08560 MemGPT]] · [[2504.19413 Mem0]] · [[2507.03724 MemOS]] · [[2601.01885 Agentic Memory]] · [[2606.22953 Plans Dont Persist]] · [[2606.23127 Managing Procedural Memory]] · [[2606.24775 Agent-Native Memory System]]

### ☁️ 推理服务与端边云 inference-serving (7)
模型切分、prefill/decode 解耦、卸载调度。→ [[inference-serving]]
- [[2209.01188 PETALS]] · [[2311.18677 Splitwise]] · [[2401.09670 DistServe]] · [[2401.14351 ServerlessLLM]] · [[2405.14371 EdgeShard]] · [[2606.15210 QLMIO Multimodal LLM Offloading]] · [[2606.17489 Online LLM Selection Bandits]]

### 💻 软件工程智能体 software-engineering (3)
赛题候选演示场景之一。→ [[software-engineering]]
- [[2307.07924 ChatDev]] · [[2405.15793 SWE-agent]] · [[2407.01489 Agentless]]

### 📊 评测基准 benchmark (12)
长程/跨域/鲁棒性评测。→ [[benchmark]]
- [[2307.13854 WebArena]] · [[2308.03688 AgentBench]] · [[2310.06770 SWE-bench]] · [[2311.12983 GAIA]] · [[2403.07718 WorkArena]] · [[2403.12031 RouterBench]] · [[2404.07972 OSWorld]] · [[2407.05291 WorkArena++]] · [[2412.14161 TheAgentCompany]] · [[2604.10866 OccuBench]] · [[2606.21140 AgentMeter]] · [[2606.22877 DynamicMem]]

### 📚 综述 survey (9)
建立统一术语与全景。→ [[survey]]
- [[2309.07864 Rise and Potential of LLM Agents Survey]] · [[2402.01680 Multi-Agents Survey]] · [[2404.11584 Landscape of AI Agent Architectures]] · [[2404.14294 Survey Efficient LLM Inference]] · [[2502.00409 Routing Strategies Survey]] · [[2502.14321 Communication-Centric Survey]] · [[2606.04990 Agent Traces to Trust Survey]] · [[2606.12191 Agentic Environment Engineering Survey]] · [[2606.19135 Agent Communication Protocols Taxonomy]]

### 🛡️ 安全与鲁棒性 safety-robustness (2)
拜占庭容错、隐性失效诊断。→ [[safety-robustness]]
- [[2606.15024 Resilient Consensus in Agentic AI]] · [[2606.22936 Premature Commitment in LLM Agents]]

## 推荐阅读路径（按团队角色）

- **#1 总体方案**：先读 [[2309.07864 Rise and Potential of LLM Agents Survey]] → [[2404.11584 Landscape of AI Agent Architectures]] → [[2502.14321 Communication-Centric Survey]] → [[2606.04990 Agent Traces to Trust Survey]]，建立全景与术语。
- **#2 拓扑/路由**：[[2402.16823 GPTSwarm]] → [[2410.11782 G-Designer]] → [[2506.02951 Adaptive Graph Pruning]] → [[2507.18224 ARG-Designer]] → [[2510.07799 GTD Graph Diffusion Topology]] → [[2410.02506 AgentPrune]]。
- **#3 记忆**：[[2307.03172 Lost in the Middle]] → [[2310.08560 MemGPT]] → [[2310.06839 LongLLMLingua]] → [[2504.19413 Mem0]] → [[2507.03724 MemOS]] → [[2601.01885 Agentic Memory]] → [[2606.24775 Agent-Native Memory System]]。
- **#4 执行引擎/工具**：[[2210.03629 ReAct]] → [[2302.04761 Toolformer]] → [[2307.16789 ToolLLM]] → [[2405.15793 SWE-agent]] → [[2407.16741 OpenHands]] → [[2303.11366 Reflexion]] → [[2606.04990 Agent Traces to Trust Survey]]。
- **#5 评测**：[[2308.03688 AgentBench]] → [[2310.06770 SWE-bench]] → [[2412.14161 TheAgentCompany]] → [[2604.10866 OccuBench]] → [[2606.21140 AgentMeter]] → [[2606.22877 DynamicMem]]。
- **#6 场景**：[[2311.12983 GAIA]] → [[2412.14161 TheAgentCompany]] → [[2604.10866 OccuBench]] → [[2307.13854 WebArena]] → [[2501.04227 Agent Laboratory]]。
- **#7 前端/演示**：[[2310.10634 OpenAgents]] → [[2407.16741 OpenHands]] → [[2606.04990 Agent Traces to Trust Survey]]（推理轨迹可视化）。

## 两条候选演示场景的文献支撑

- **场景 A · 系统级软件工程自动化**：[[2310.06770 SWE-bench]] · [[2405.15793 SWE-agent]] · [[2407.01489 Agentless]] · [[2407.16741 OpenHands]] · [[2307.07924 ChatDev]] · [[2308.00352 MetaGPT]] · [[2606.10662 DeLM Decentralized MAS]]
- **场景 B · 跨域多模态投研 / 数字劳动力**：[[2311.12983 GAIA]] · [[2501.04227 Agent Laboratory]] · [[2412.14161 TheAgentCompany]] · [[2604.10866 OccuBench]] · [[2403.07718 WorkArena]] · [[2303.17580 HuggingGPT]]
