---
type: theme
tags:
  - theme
  - agent-framework
---

# 主题：智能体框架与平台 (agent-framework)

多 agent 编排与通用 agent 平台——赛题底座选型与组织架构设计的参照。

## 三条脉络
**A. LLM 作控制器调度专家**：[[2303.17580 HuggingGPT]]（LLM 控制器+HF 专家）、[[2411.04468 Magentic-One]]（Orchestrator 主导+专门 agent+重规划）、[[2501.04227 Agent Laboratory]]（三阶段研究 pipeline）。
**B. 角色扮演与 SOP 协作**：[[2303.17760 CAMEL]]（角色扮演+inception prompting）、[[2308.00352 MetaGPT]]（SOP+结构化交接）、[[2307.07924 ChatDev]]（chat chain+去幻觉）、[[2308.10848 AgentVerse]]（动态招募专家）。
**C. 平台/系统**：[[2308.08155 AutoGen]]（conversable agent 通用框架）、[[2310.10634 OpenAgents]]（开源平台+Web UI）、[[2402.14034 AgentScope]]（容错+actor 分布式）、[[2407.16741 OpenHands]]（事件流+Docker 沙箱+CodeAct）、[[2304.03442 Generative Agents]]（记忆/反思/检索经典架构）、[[2305.16291 VOYAGER]]（技能库+课程终身学习）。

## 综合洞察
- **打分明确惩罚"直接套用开源框架"**：AutoGen/OpenHands 等可作底座候选但需深度重构，执行引擎(#4)尤其应自研以体现"底层突破"。
- **结构化交接抑制噪声**：MetaGPT 的 SOP+结构化产物、ChatDev 的 chat chain 是低熵通信早期实践——但拓扑静态，需升级为动态图。
- **容错一等公民**：AgentScope 把容错防级联纳入平台，罕见且贴合赛题；OpenHands 的 Docker 沙箱直接服务鲁棒容错演示。
- **动态组队**：AgentVerse 的"动态招募"向"摒弃静态组队"迈出一步，是赛题动态拓扑的起点。

## 与赛题关联
> 支柱：低熵通信 / 鲁棒容错 / 组织架构打分点
- 组织层可借鉴 MetaGPT/Magentic-One 的层级分工与 Orchestrator 重规划，但拓扑须动态生成。
- 执行引擎可借鉴 OpenHands 沙箱+事件流、AgentScope actor 分布式与容错。
- Generative Agents 的记忆/反思/检索与 VOYAGER 的技能库是记忆与程序性记忆的范本。

## 全部笔记
[[2303.17580 HuggingGPT]] · [[2303.17760 CAMEL]] · [[2304.03442 Generative Agents]] · [[2305.16291 VOYAGER]] · [[2308.00352 MetaGPT]] · [[2308.08155 AutoGen]] · [[2308.10848 AgentVerse]] · [[2310.10634 OpenAgents]] · [[2402.14034 AgentScope]] · [[2407.16741 OpenHands]] · [[2411.04468 Magentic-One]] · [[2501.04227 Agent Laboratory]]
