---
type: theme
tags:
  - theme
  - benchmark
---

# 主题：评测基准 (benchmark)

赛题"可运行系统验证"与评测体系(#5)的参照。趋势：从字符串匹配→功能正确性→长程→鲁棒性注入。

## 谱系
**A. 通用 agent 能力**
- [[2308.03688 AgentBench]]：8 环境评测 LLM-as-Agent，诊断长程推理/决策是主要障碍。
- [[2311.12983 GAIA]]：对人简单对 AI 难，proof-of-work 式易验证答案，人类 92% vs GPT-4 15%。

**B. Web / 企业 / 职业**
- [[2307.13854 WebArena]]：真实自托管 Web，功能验证，GPT-4 14% vs 人类 78%。
- [[2403.07718 WorkArena]] / [[2407.05291 WorkArena++]]：ServiceNow 企业知识工作，33→682 复合任务。
- [[2412.14161 TheAgentCompany]]：模拟软件公司 175 职业任务，长程，最强 30%。
- [[2604.10866 OccuBench]]：100 职业/65 域，LES 模拟环境，**故障注入**评测鲁棒性。
- [[2404.07972 OSWorld]]：真实 OS 跨应用，人类 72% vs 最强 12%。

**C. 软件/工具/路由**
- [[2310.06770 SWE-bench]]：真实 GitHub issue + 单元测试。
- [[2403.12031 RouterBench]]：多 LLM 路由评测，405k 推理结果。
- [[2606.21140 AgentMeter]]：模型-CLI 匹配，成本感知 AMS 指标。

**D. 长程记忆**
- [[2606.22877 DynamicMem]]：15 月/2.2M token 用户轨迹，>93% 失败在检索。

## 综合洞察
- **功能正确性 > 字符串匹配**：WebArena/SWE-bench/OSWorld 用执行式验证器。
- **鲁棒性评测是稀缺且关键**：仅 OccuBench 系统做故障注入（显式/隐式/混合）——赛题"接受异常注入"的直接范本。
- **长程鸿沟巨大**：多数基准最强 agent 远逊人类（14%/12%/30%），论证赛题鲁棒容错必要性。
- **LES 思想**：用 LLM 模拟环境，把环境构建从工程变配置——赛题可低成本覆盖多域。

## 与赛题关联
> 支柱：④ 鲁棒容错 / 多任务演示 / 评测体系
- 评测体系(#5)：多环境+功能验证+部分评分（TheAgentCompany）+故障注入（OccuBench）。
- 场景任务来源：SWE-bench(SE) + GAIA/TheAgentCompany/OccuBench(投研/数字劳动力)。
- 效率指标参考 AgentMeter 的成本感知 AMS（成功锚定+昂贵失败惩罚）。

## 全部笔记
[[2307.13854 WebArena]] · [[2308.03688 AgentBench]] · [[2310.06770 SWE-bench]] · [[2311.12983 GAIA]] · [[2403.07718 WorkArena]] · [[2403.12031 RouterBench]] · [[2404.07972 OSWorld]] · [[2407.05291 WorkArena++]] · [[2412.14161 TheAgentCompany]] · [[2604.10866 OccuBench]] · [[2606.21140 AgentMeter]] · [[2606.22877 DynamicMem]]
