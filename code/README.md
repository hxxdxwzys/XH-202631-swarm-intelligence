# 代码骨架

当前处于架构设计阶段，**端-边-云自适应调度模块（角色 #2）v0.1 已实现**，其余模块待实现。

## 结构

```
code/
└── core/
    └── scheduler/          # 端-边-云自适应调度（角色 #2，v0.1 可运行）
        ├── models.py       # 资源层/模型/子任务/决策
        ├── metrics.py      # 时延/成本/隐私满足率
        ├── split.py        # EdgeShard 式层切分
        ├── ports.py        # #1/#3/#4 抽象接口
        ├── scheduler.py    # 两阶段调度器
        ├── sim.py          # 单机模拟 + 演示
        ├── tests/          # 单元测试
        └── README.md
```

## 运行

```bash
cd code
python -m core.scheduler.sim                              # 调度演示
python -m unittest core.scheduler.tests.test_scheduler    # 单元测试
```

## 待实现模块（对应分工）

- `core/orchestrator/` 编排器（#1）
- `core/router/` 动态拓扑路由（#3）
- `core/memory/` 分布式记忆 + 压缩唤醒（#1）
- `core/executor/` 执行引擎 + 工具接口 + 异常重试（#4）
- `adapters/` 模型适配层（多 LLM 兼容，#6）
- `eval/` 评测脚本（#5）
- `frontend/` 推理轨迹可视化（#8）
