---
type: theme
tags:
  - theme
  - inference-serving
---

# 主题：推理服务与端边云 (inference-serving)

**赛题核心支柱③**。模型切分、prefill/decode 解耦、云-边-端卸载调度——"依据子任务实时性与数据敏感等级自动完成推理位置动态选择与模型切分"。

## 方法谱系
**A. 协同/分层推理**
- [[2209.01188 PETALS]]：层切分到异构节点+流水线并行，消费级 GPU 跑 176B。
- [[2405.14371 EdgeShard]]：模型分 shard 到端/边/云，动态规划选设备与切分点，延迟降 50%。

**B. 阶段解耦**
- [[2311.18677 Splitwise]] / [[2401.09670 DistServe]]：prefill/decode 分机，消除干扰，goodput 大升。

**C. 冷启动/局部性**
- [[2401.14351 ServerlessLLM]]：多级本地 checkpoint 缓存+局部性调度+活迁移，冷启动降 10-200x。

**D. 卸载决策**
- [[2606.15210 QLMIO Multimodal LLM Offloading]]：云-边异构 MLLM，质量-延迟预测联合优化，延迟降 58%。
- [[2606.17489 Online LLM Selection Bandits]]：受限 bandit 在线选模型，硬预算+软 SLA。

**E. 全景**
- [[2404.14294 Survey Efficient LLM Inference]]：数据/模型/系统三层高效推理 taxonomy。

## 综合洞察
- **按阶段/按层切分到异构节点**是端边云调度的核心范式：prefill 偏云(算力)、decode 偏边(访存)、层 shard 到端/边/云。
- **预测驱动调度**：QLMIO(质量-延迟预测)、bandit(在线学习) 把"放哪儿跑"从启发式变为优化问题。
- **冷启动与活迁移**服务鲁棒容错：节点失效时快速在另一节点拉起（ServerlessLLM）。
- 荣耀是终端公司，端侧/边侧能力展示对"应用契合度"加分。

## 与赛题关联
> 支柱：③ 端边云调度（核心）/ ④ 鲁棒容错 / 效率
- 执行引擎(#4)调度钩子：`execute(node)` 位置透明，按 EdgeShard 切分 + QLMIO 预测 + bandit 在线选模型。
- 即使演示单机，用"带标签的区"模拟端-边-云切分，让评委看到调度决策。
- 推理位置选择与"模型切分"应写入材料伪代码与复杂性分析（交付物要求）。

## 全部笔记
[[2209.01188 PETALS]] · [[2311.18677 Splitwise]] · [[2401.09670 DistServe]] · [[2401.14351 ServerlessLLM]] · [[2405.14371 EdgeShard]] · [[2606.15210 QLMIO Multimodal LLM Offloading]] · [[2606.17489 Online LLM Selection Bandits]] · [[2404.14294 Survey Efficient LLM Inference]]
