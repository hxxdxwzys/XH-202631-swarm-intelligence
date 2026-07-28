# 端-边-云自适应调度模块（角色 #2）

实现《端边云调度模块设计.md》§6。**v0.2** 在 v0.1 基础上补齐在线自适应、阶段切分、事件日志与配置化。

## 文件

| 文件 | 职责 | 设计节 |
|------|------|--------|
| `models.py` | 资源层/模型/子任务/决策数据模型 | §6.1–6.3 |
| `metrics.py` | 时延/资源开销/隐私满足率（单层、层切分、阶段切分） | §6.4 |
| `split.py` | 层切分（EdgeShard 式枚举寻优）+ 阶段切分（prefill/decode） | §6.3.3 |
| `scheduler.py` | 两阶段调度器（`_feasible` + `_select`，可覆盖） | §6.3 |
| `bandit.py` | 受限上下文 bandit（UCB1，硬预算+软 SLA） | §6.3.2 |
| `adaptive.py` | `AdaptiveScheduler`：bandit 做 stage-2 在线选择 + 反馈学习 | §6.3.2 |
| `events.py` | 结构化调度事件日志（JSONL，推理轨迹） | §6.5 |
| `config.py` | 从 dict/JSON 加载资源环境 | §6.1 |
| `sim.py` | 单机模拟三层 + mock 执行 + 演示（规则 + 自适应） | §6.1 |
| `default_env.json` | 资源参数表示例配置 | §6.1 |
| `tests/` | 16 项单元测试 | — |

## 运行

```bash
cd code
python -m core.scheduler.sim                                            # 演示（规则 + bandit 学习）
python -m unittest core.scheduler.tests.test_scheduler \                 # 全部测试
                 core.scheduler.tests.test_bandit \
                 core.scheduler.tests.test_split \
                 core.scheduler.tests.test_events \
                 core.scheduler.tests.test_config
```

## 设计要点

- **两阶段调度**（§6.3）：隐私硬筛（σ_w → 允许层）→ 能力/显存/时延可行域 → stage-2 选择。
  - 基类 `Scheduler`：stage-2 用代价函数 $J=\alpha\cdot\text{Lat}/\tau+\beta\cdot\text{Cost}+\gamma\cdot(1-\kappa)$。
  - `AdaptiveScheduler`：stage-2 用 bandit，从 #4 执行反馈学习"哪个 arm 回报最高"。
- **模型切分**（§6.3.3）：单层显存放不下时，层切分（块分配寻优，受各层显存约束）与阶段切分（prefill→强算力层、decode→低时延层）择优。
- **隐私硬约束**：L2 敏感禁上云、L3 机密仅端侧，由 `allowed_layer_kinds` 强制，`privacy_satisfaction` 度量。
- **在线自适应**（§6.3.2）：以 (s_w, σ_w) 为上下文的受限 bandit，硬预算（packing）+ 软 SLA（covering），UCB1 平衡探索-利用。
- **推理轨迹**（§6.5）：`ScheduleLogger` 把每条决策记为 typed 事件写 JSONL，供 #5/#7/#8 回放与可视化。
- **配置化**：`default_env.json` 可按实际算力标定，不改代码。

## 演示结果

规则演示 5 种决策路径：层切分 / 端侧 / 云端 / 边缘 / 不可行（回送重规划），P_priv=100%。
自适应演示：(S2,L1) 上下文 bandit 序列 `[8B, 30B×7]`，收敛到质量最高的云端 30B（0.875 占比）。

## 复杂性分析（对应附录 B）

设资源层数 $n=|L|$（≤3）、模型总数 $\Phi=\sum|\Phi_\ell|$、模型块数 $K$（~48）。

| 算法 | 时间复杂度 | 说明 |
|------|-----------|------|
| `schedule` 单层路径 | $O(n\cdot\overline{|\Phi_\ell|})$ | 阶段一可行域筛选 |
| `best_layer_split` | $O\!\big(\binom{K+n-1}{n-1}\cdot n\big)$ | 枚举块分配；n=3,K=48 约 $3.7\times10^3$，受显存剪枝后更少 |
| `best_phase_split` | $O(n^2)$ | 枚举 (prefill, decode) 层对 |
| `ContextualBandit.select/update` | $O(\|\text{arms}\|)$ / $O(1)$ | 每次调度常数级开销 |

空间：$O(n\cdot\overline{|\Phi_\ell|})$ + bandit 统计 $O(|\text{ctx}|\cdot\|\text{arms}\|)$。单子任务调度整体轻量；切分仅在单层不可行时触发。

## v0.3 待补

- 与 #1 规划器、#4 执行引擎真实接口对接（替换 mock，由组长整合时统一）。
- bandit 奖励引入成本/时延复合效用与需求变更感知。
- 真实多机三层部署（当前为单机模拟）。
