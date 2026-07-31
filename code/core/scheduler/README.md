# 端-边-云自适应调度模块（角色 #2）

实现《端边云调度模块设计.md》§6。当前版本 **v0.5**——自洽可运行、全量测试、性能基准验证。

## 版本演进

| 版本 | 核心 | 状态 |
|------|------|------|
| v0.1 | 数据模型 + 两阶段调度 + 层切分 + 指标 + 接口 | ✅ |
| v0.2 | bandit 在线自适应 + 阶段切分 + 事件日志 + 配置化 | ✅ |
| v0.3 | 时间均衡（LPT makespan + 负载感知 + 关键路径） | ✅ |
| v0.4 | DAG 感知运行时（依赖就绪 + 死锁检测 + 批量调度） | ✅ |
| v0.5 | 集成测试 + 性能基准 + 文档定稿 | ✅ |

## 文件

| 文件 | 职责 |
|------|------|
| `models.py` | 资源层/模型/子任务/决策（§6.1-6.3） |
| `metrics.py` | 时延/成本/隐私满足率 + makespan/均衡度/空闲率 |
| `split.py` | 层切分 + 阶段切分（§6.3.3） |
| `scheduler.py` | 两阶段调度器（J 含负载项） |
| `bandit.py` | 受限上下文 bandit（UCB1，硬预算+软SLA） |
| `adaptive.py` | AdaptiveScheduler：bandit 在线选择 + 反馈学习 |
| `balancer.py` | LoadTracker + BatchScheduler（LPT makespan）+ critical_path |
| `runtime.py` | SchedulerRuntime：DAG 事件驱动循环 + 依赖就绪 + 死锁检测 |
| `events.py` | 结构化事件日志（JSONL，推理轨迹） |
| `config.py` | 资源环境从 dict/JSON 加载 |
| `sim.py` | 单机模拟 + 4 种演示（规则/自适应/时间均衡/DAG运行时） |
| `default_env.json` | 资源参数表示例 |
| `tests/` | **35 项单元测试 + 集成测试 + 性能基准** |

## 运行

```bash
cd code
python -m core.scheduler.sim                   # 全部演示
python -m unittest core.scheduler.tests.test_scheduler \
                 core.scheduler.tests.test_bandit \
                 core.scheduler.tests.test_split \
                 core.scheduler.tests.test_events \
                 core.scheduler.tests.test_config \
                 core.scheduler.tests.test_balancer \
                 core.scheduler.tests.test_runtime \
                 core.scheduler.tests.test_integration    # 全部测试
```

## 核心能力

| 能力 | 实现 | 赛题对齐 |
|------|------|---------|
| 两阶段调度 | 隐私硬筛→可行域→代价J最优 | 按子任务量与隐私程度调配模型 |
| 模型切分 | 层切分（EdgeShard DP）+ 阶段切分（prefill/decode） | 模型切分/端云协同 |
| 在线自适应 | 受限上下文 bandit，从执行反馈学习 | 自适应调配 |
| 时间均衡 | LPT makespan 优化 + 负载追踪 + 关键路径 | token与时间效率 |
| DAG 运行时 | 依赖就绪+批量调度+死锁检测+事件日志 | 系统闭环 |
| 隐私硬约束 | L2禁云、L3仅端，P_priv可量化 | 数据敏感约束 |
| 推理轨迹 | JSONL 事件日志，可回放可可视化 | 展示中间决策过程 |
| 配置化 | JSON 标定算力，不改代码 | 可扩展性 |

## 演示结果

| 演示 | 结果 |
|------|------|
| 规则调度 | 5 种决策路径，P_priv=100% |
| bandit 自适应 | [8B→30B×7] 收敛至云端 30B（0.875） |
| 时间均衡 | makespan +22.2%、均衡度 +99.3%、空闲率 −44.3% |
| DAG 运行时 | 菱形 DAG 4/4 完成，关键路径 {A,B,D} 正确 |

## 性能基准

| 任务数 | 总耗时 | 单任务开销 |
|--------|--------|-----------|
| 10 | 0.06ms | 0.006ms |
| 100 | 0.43ms | 0.004ms |
| 500 | 4.79ms | 0.010ms |

**结论：调度器自身开销 < 0.01ms/任务，远低于任务执行时间，不构成瓶颈。**

## 复杂性分析（附录 B）

设层数 n（≤3）、模型数 Φ、块数 K（~48）、批量任务数 m、DAG 节点 |W|、边 |A|。

| 算法 | 时间复杂度 |
|------|-----------|
| `schedule` 单层 | O(n·Φ̄) |
| `best_layer_split` | O(C(K+n-1,n-1)·n) |
| `best_phase_split` | O(n²) |
| `BatchScheduler.schedule_batch` | O(m·n·Φ̄ + m·log m) |
| `critical_path` | O(\|W\| + \|A\|) |
| `SchedulerRuntime.run` | O(\|W\|·(n·Φ̄ + log m)) |
| `Bandit.select/update` | O(\|arms\|) / O(1) |
