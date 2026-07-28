# 端-边-云自适应调度模块（角色 #2）

实现《端边云调度模块设计.md》§6 的 v0.1 可运行最小版。

## 文件

| 文件 | 职责 | 对应设计节 |
|------|------|-----------|
| `models.py` | 资源层/模型/子任务/决策数据模型 | §6.1–6.3 |
| `metrics.py` | 时延、资源开销、隐私满足率 | §6.4 |
| `split.py` | EdgeShard 式层切分（块分配寻优） | §6.3.3 |
| `ports.py` | #1/#3/#4 抽象接口（Protocol） | §6.5 |
| `scheduler.py` | 两阶段调度器 | §6.3 |
| `sim.py` | 单机模拟三层 + mock 执行 + 演示 | §6.1 |

## 运行

```bash
cd code
python -m core.scheduler.sim                 # 端到端演示
python -m unittest core.scheduler.tests.test_scheduler   # 单元测试
```

## 设计要点

- **两阶段调度**：隐私硬筛（σ_w → 允许层）→ 能力/显存/时延可行域 → 代价函数 J 最优。
- **模型切分**：单层显存放不下大模型时，跨层切分（枚举求最优块分配，受各层显存容量约束）。
- **隐私硬约束**：L2 敏感禁上云、L3 机密仅端侧，由 `allowed_layer_kinds` 强制。
- **单机模拟**：`default_env()` 用带标签的"区"模拟端/边/云，架构对真实三层透明。

## v0.2 待补

- 受限 bandit 在线模型选择（硬预算 + 软 SLA，从 #4 反馈学习）。
- 阶段切分（prefill/decode 解耦，Splitwise/DistServe 式）。
- 与 #1 规划器、#4 执行引擎的真实接口对接（替换 mock）。
