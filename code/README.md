# 代码

**端-边-云自适应调度模块（角色 #2）v0.2 已实现**（1187 行 / 16 测试全过），其余模块待实现。

## 结构

```
code/
└── core/
    └── scheduler/                 # 端-边-云自适应调度（角色 #2，v0.2）
        ├── models.py              # 资源层/模型/子任务/决策（§6.1-6.3）
        ├── metrics.py             # 时延/成本/隐私满足率（单层/层切分/阶段切分）（§6.4）
        ├── split.py               # 层切分 + 阶段切分（§6.3.3）
        ├── scheduler.py           # 两阶段调度器（§6.3）
        ├── bandit.py              # 受限上下文 bandit（UCB1，硬预算+软SLA）（§6.3.2）
        ├── adaptive.py            # AdaptiveScheduler：bandit 在线选择 + 反馈学习
        ├── ports.py               # #1/#3/#4 抽象接口（§6.5）
        ├── events.py              # 结构化调度事件日志（JSONL，推理轨迹）
        ├── config.py              # 资源环境从 dict/JSON 加载
        ├── default_env.json       # 资源参数表示例
        ├── sim.py                 # 单机模拟三层 + mock 执行 + 演示
        ├── README.md              # 模块说明 + 复杂性分析（附录B）
        └── tests/                 # 16 项单元测试
```

## 运行

```bash
cd code
python -m core.scheduler.sim                                            # 演示（规则 + bandit 学习）
python -m unittest core.scheduler.tests.test_scheduler \
                 core.scheduler.tests.test_bandit \
                 core.scheduler.tests.test_split \
                 core.scheduler.tests.test_events \
                 core.scheduler.tests.test_config                       # 全部测试
```

## 已实现能力

- **两阶段调度**：隐私硬筛 → 能力/显存/时延可行域 → 代价 J / bandit 选择
- **模型切分**：层切分（EdgeShard 式枚举寻优）+ 阶段切分（prefill/decode）择优
- **在线自适应**：受限上下文 bandit，从执行反馈学习，硬预算 + 软 SLA
- **隐私硬约束**：L2 禁云、L3 仅端，P_priv 指标可测
- **推理轨迹**：JSONL 事件日志，供 #5/#7/#8 回放与可视化
- **配置化**：`default_env.json` 标定实际算力

## 集成

组长对接其它模块时看 **`docs/调度模块集成指南.md`**——列明了该看什么、改什么（4 个接口契约 + 替换 mock 清单 + 待拍板参数）。

## 待实现模块（对应分工）

- `core/orchestrator/` 编排器（#1）
- `core/router/` 动态拓扑路由（#3）
- `core/memory/` 分布式记忆 + 压缩唤醒（#1）
- `core/executor/` 执行引擎 + 工具接口 + 异常重试（#4）
- `adapters/` 模型适配层（多 LLM 兼容，#6）
- `eval/` 评测脚本（#5）
- `frontend/` 推理轨迹可视化（#8）
