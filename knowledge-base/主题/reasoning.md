---
type: theme
tags:
  - theme
  - reasoning
---

# 主题：推理范式 (reasoning)

单体 LLM 如何"慢思考"——从线性链到树/图/MCTS 搜索的演进。这是 agent 单步推理的内核，也是长程任务的基本步。

## 演进主线
1. **线性链** [[2201.11903 Chain-of-Thought Prompting]]：few-shot 示范中间步骤，大模型涌现推理。
2. **多路径投票** [[2203.11171 Self-Consistency]]：采样多条推理路径取多数，无训练提分。
3. **分解求解** [[2205.10625 Least-to-Most Prompting]]：先分解为从易到难子问题再顺序解，攻 easy-to-hard 泛化。
4. **神经符号分工** [[2211.10435 PAL Program-aided Language Models]] / [[2211.12588 Program of Thoughts]]：LLM 生成程序、解释器算，解耦推理与计算。
5. **树搜索** [[2305.10601 Tree of Thoughts]]：思维树 + LM 自评 + BFS/DFS 回溯，System-2 审慎。
6. **图推理** [[2308.09687 Graph of Thoughts]]：思维任意图，聚合/蒸馏/反馈，统一并推广 CoT/ToT。
7. **统一搜索** [[2310.04406 LATS Language Agent Tree Search]]：MCTS 统一推理+动作+规划，配 LM 价值函数与反思。

## 综合洞察
- 范式从"线性→树→图"逐步解除结构刚性，搜索与自评是核心杠杆。
- **成本权衡**：搜索/多路径带来高 token 开销——长程任务须仅在高风险分叉点启用，否则 token 爆炸（与赛题效率项冲突）。
- **神经符号分工**（PAL/PoT）对赛题执行引擎有直接价值：数值/逻辑子任务生成程序由解释器执行，消除 LLM 计算噪声。

## 与赛题关联
> 支柱：鲁棒容错 / 长程记忆
- ToT/LATS 的"自评+回溯"是鲁棒容错在推理层的体现，走错可退回重选。
- Least-to-Most 的"分解→顺序求解"是超长程任务规划骨架，可与记忆层结合防遗忘。
- 这些范式是单 agent 单步推理；赛题需把它们扩展为多 agent 异构拓扑上的协同推理。

## 全部笔记
[[2201.11903 Chain-of-Thought Prompting]] · [[2203.11171 Self-Consistency]] · [[2205.10625 Least-to-Most Prompting]] · [[2211.10435 PAL Program-aided Language Models]] · [[2211.12588 Program of Thoughts]] · [[2305.10601 Tree of Thoughts]] · [[2308.09687 Graph of Thoughts]] · [[2310.04406 LATS Language Agent Tree Search]]
