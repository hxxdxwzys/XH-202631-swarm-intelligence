# 代码

**端-边-云自适应调度模块（角色 #2）v0.5 已实现**（1884 行 / 35 测试全过），其余模块待实现。

## 结构

```
code/
└── core/
    └── scheduler/                 # 端-边-云自适应调度（角色 #2，v0.5）
        ├── models.py              # 资源层/模型/子任务/决策
        ├── metrics.py             # 时延/成本/隐私 + makespan/均衡度/空闲率
        ├── split.py               # 层切分 + 阶段切分
        ├── scheduler.py           # 两阶段调度器（J 含负载项）
        ├── bandit.py              # 受限上下文 bandit
        ├── adaptive.py            # 自适应调度器（bandit 在线学习）
        ├── balancer.py            # LPT 批量调度 + 负载追踪 + 关键路径
        ├── runtime.py             # DAG 事件驱动运行时
        ├── ports.py               # #1/#3/执行框架 抽象接口
        ├── events.py              # 结构化事件日志（JSONL）
        ├── config.py              # 资源环境配置化
        ├── default_env.json       # 资源参数表示例
        ├── sim.py                 # 4 种演示（规则/自适应/时间均衡/DAG运行时）
        ├── README.md              # 模块说明 + 复杂性分析 + 性能基准
        └── tests/                 # 35 项测试（含集成测试 + 性能基准）
```

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

## v0.1–v0.5 演进

| 版本 | 核心 |
|------|------|
| v0.1 | 数据模型 + 两阶段调度 + 层切分 + 指标 + 接口 |
| v0.2 | bandit 在线自适应 + 阶段切分 + 事件日志 + 配置化 |
| v0.3 | 时间均衡（LPT makespan + 负载感知 + 关键路径） |
| v0.4 | DAG 感知运行时（依赖就绪 + 死锁检测 + 批量调度） |
| v0.5 | 集成测试 + 性能基准（<0.01ms/任务） + 文档定稿 |

## 待实现模块（对应新分工）

- `core/orchestrator/` 编排器
- `core/router/` 动态拓扑路由（#3）
- `core/memory/` 分布式记忆 + 压缩唤醒（#1）
- `core/heterogeneous/` 智能体异构设计（#4）
- `core/fault_tolerance/` 神经符号协同推理内生容错（#5）
- `adapters/` 模型适配层（#6）
- `eval/` 评测脚本（#7）
- `frontend/` 推理轨迹可视化（#8）
