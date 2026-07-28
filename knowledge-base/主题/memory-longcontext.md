---
type: theme
tags:
  - theme
  - memory-longcontext
---

# 主题：记忆与长上下文 (memory-longcontext)

**赛题核心支柱①**。分布式记忆、上下文压缩唤醒、抗遗忘——"不依赖单一模型长窗口无损外推"。

## 问题诊断（为什么需要）
- [[2307.03172 Lost in the Middle]]：长上下文 U 型曲线，中间信息丢失。
- [[2606.22953 Plans Dont Persist]]：计划是"上下文驻留"非"持久状态"，驱逐即丢，朴素驱逐 -34.7pp。
- [[2606.22877 DynamicMem]]：>93% 失败源于检索而非生成。

## 方法谱系
**A. 上下文压缩**
- [[2310.05736 LLMLingua]]：coarse-to-fine 压缩，20x 几乎无损。
- [[2310.06839 LongLLMLingua]]：问题感知压缩+重排，1/4 token 提升 21.4%。

**B. 分层/虚拟记忆**
- [[2310.08560 MemGPT]]：OS 虚拟内存分页，分层存储+函数调用自管理。
- [[2304.03442 Generative Agents]]：recency/importance/relevance 检索 + 周期反思。
- [[2305.10250 MemoryBank]]：艾宾浩斯遗忘曲线，选择性遗忘/强化。

**C. 生产级/图记忆**
- [[2504.19413 Mem0]]：动态抽取整合+图记忆，p95 延迟降 91%、token 省 90%+。
- [[2507.03724 MemOS]]：记忆 OS，统一明文/激活/参数级记忆，MemCube 抽象。

**D. 端到端/程序性**
- [[2601.01885 Agentic Memory]]：LTM+STM 统一进策略，记忆操作工具化+RL(GRPO)。
- [[2606.23127 Managing Procedural Memory]]：程序性记忆跨任务/角色/模型迁移，多模型 diverse 经验最泛化。

**E. 系统评测**
- [[2606.24775 Agent-Native Memory System]]：四模块(存储/抽取/检索路由/维护)分解，12 系统评测，无单一架构通吃。

## 综合洞察
- **检索 > 写入**：DynamicMem 证明失败主要在检索/唤醒，记忆层重点应是"高质量唤醒"。
- **关键信息须显式持久化**：Plans Don't Persist 警示全局目标/计划不能只靠上下文窗口，须周期重唤醒。
- **遗忘是必需**：千步任务不可能全量保留，须按重要性+时间遗忘/压缩防膨胀（MemoryBank）。
- **统一管理**：AgeMem/MemOS 把记忆操作工具化、统一 LTM/STM——agent 自主决定存/取/弃。

## 与赛题关联
> 支柱：① 长程记忆（核心）/ 效率
- 记忆层(#3)架构选型：MemGPT(分层分页) / Mem0(抽取+图) / MemOS(统一 OS) / AgeMem(工具化+RL) 四选一或组合。
- 检索打分用 Generative Agents 三因子；压缩唤醒用 LongLLMLingua（问题感知+重排缓解 lost-in-middle）。
- 检查点 = 记忆一部分（与执行引擎 #4 接口）；程序性记忆沉淀可复用技能（VOYAGER/AFTER）。

## 全部笔记
[[2305.10250 MemoryBank]] · [[2307.03172 Lost in the Middle]] · [[2310.05736 LLMLingua]] · [[2310.06839 LongLLMLingua]] · [[2310.08560 MemGPT]] · [[2504.19413 Mem0]] · [[2507.03724 MemOS]] · [[2601.01885 Agentic Memory]] · [[2606.22953 Plans Dont Persist]] · [[2606.23127 Managing Procedural Memory]] · [[2606.24775 Agent-Native Memory System]]
