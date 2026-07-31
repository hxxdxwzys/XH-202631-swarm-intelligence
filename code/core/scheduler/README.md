# 端-边-云自适应调度模块（角色 #2）

实现《端边云调度模块设计.md》§6。**v0.3** 在 v0.2 基础上新增时间均衡（负载感知 + makespan 优化 + 关键路径）。

## 文件

| 文件 | 职责 | 设计节 |
|------|------|--------|
| `models.py` | 资源层/模型/子任务/决策数据模型 | §6.1–6.3 |
| `metrics.py` | 时延/成本/隐私满足率 + makespan/均衡度/空闲率 | §6.4 + v0.3 |
| `split.py` | 层切分 + 阶段切分 | §6.3.3 |
| `scheduler.py` | 两阶段调度器（J 含可选负载项） | §6.3 |
| `bandit.py` | 受限上下文 bandit（UCB1，硬预算+软 SLA） | §6.3.2 |
| `adaptive.py` | `AdaptiveScheduler`：bandit 在线选择 + 反馈学习 | §6.3.2 |
| `balancer.py` | `LoadTracker` + `BatchScheduler`（LPT makespan）+ `critical_path` | v0.3 |
| `events.py` | 结构化调度事件日志（JSONL，推理轨迹） | §6.5 |
| `config.py` | 从 dict/JSON 加载资源环境 | §6.1 |
| `sim.py` | 单机模拟 + 演示（规则/自适应/时间均衡） | §6.1 |
| `default_env.json` | 资源参数表示例 | §6.1 |
| `tests/` | 23 项单元测试 | — |

## 运行

```bash
cd code
python -m core.scheduler.sim                   # 演示（规则 + bandit + 时间均衡）
python -m unittest core.scheduler.tests.test_scheduler \
                 core.scheduler.tests.test_bandit \
                 core.scheduler.tests.test_split \
                 core.scheduler.tests.test_events \
                 core.scheduler.tests.test_config \
                 core.scheduler.tests.test_balancer    # 全部测试
```

## 设计要点

- **两阶段调度**（§6.3）：隐私硬筛 → 可行域 → 代价函数 J（α·Lat/τ + β·Cost + γ·(1−κ) + δ·Load）。
- **模型切分**（§6.3.3）：层切分 + 阶段切分择优。
- **在线自适应**（§6.3.2）：受限上下文 bandit，从执行反馈学习。
- **时间均衡**（v0.3）：
  - `BatchScheduler`：LPT 策略最小化批量 makespan（重任务先派到最快层，负载满了换次快层）
  - `LoadTracker`：追踪各层负载，支撑负载感知
  - `critical_path`：DAG 关键路径识别，关键任务优先快模型
  - 三指标：makespan / 负载均衡度（Jain 公平指数）/ 空闲率
- **隐私硬约束**：L2 禁上云、L3 仅端侧。
- **推理轨迹**（§6.5）：JSONL 事件日志。
- **配置化**：`default_env.json` 标定实际算力。

## 演示结果

| 演示 | 结果 |
|------|------|
| 规则调度 | 5 种决策路径（切分/端/云/边/不可行），P_priv=100% |
| bandit 自适应 | (S2,L1) 序列 [8B→30B×7]，收敛至云端 30B（0.875） |
| 时间均衡 | makespan **+22.2%**、均衡度 **+99.3%**、空闲率 **−44.3%**（9 任务批量 vs 逐任务） |

## 复杂性分析（附录 B）

设层数 n（≤3）、模型总数 Φ、块数 K（~48）、批量任务数 m。

| 算法 | 时间复杂度 | 说明 |
|------|-----------|------|
| `schedule` 单层路径 | O(n·Φ̄) | 阶段一可行域筛选 |
| `best_layer_split` | O(C(K+n-1,n-1)·n) | 枚举块分配 |
| `best_phase_split` | O(n²) | 枚举层对 |
| `BatchScheduler.schedule_batch` | O(m·n·Φ̄ + m·log m) | LPT 排序 + 逐任务选最早完成层 |
| `critical_path` | O(\|W\| + \|A\|) | 拓扑排序 + 最长路径 DP |
| `ContextualBandit.select/update` | O(\|arms\|) / O(1) | 每次调度常数级 |

## v0.4 待补

- DAG 感知运行时（`SchedulerRuntime`：事件驱动循环，依赖就绪检查，完成触发重调度）
- 关键路径优先调度器（CriticalPathScheduler：关键任务快模型、非关键高质量）
- 异步执行接口
