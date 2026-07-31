"""单机模拟三层资源环境 + mock 执行引擎 + 端到端演示。
用带标签的"区"模拟端/边/云（§6.1：演示以单机模拟为主，架构按真实三层设计）。"""
from __future__ import annotations
import random
from core.scheduler.models import (
    ResourceEnvironment, ResourceLayer, ModelProfile, Subtask,
    ComputeScale, LatencyTier, SensitivityLevel, ScheduleDecision,
)
from core.scheduler.scheduler import Scheduler
from core.scheduler.adaptive import AdaptiveScheduler
from core.scheduler.bandit import ContextualBandit
from core.scheduler.balancer import BatchScheduler, LoadTracker
from core.scheduler.runtime import SchedulerRuntime
from core.scheduler.events import ScheduleLogger
from core.scheduler.metrics import (
    privacy_satisfaction, makespan, load_balance_index, idle_ratio,
)
from core.scheduler.ports import ExecutorPort, ExecutionResult


def default_env() -> ResourceEnvironment:
    """默认资源参数表（§6.1，参考 EdgeShard/QLMIO 口径，可按实际算力标定）。"""
    end = ResourceLayer(
        name="终端", kind="end", compute_tps=200.0, mem_gb=12.0,
        rtt_ms=2.0, cost_per_1k_tok=0.0,
        models=(
            ModelProfile("Qwen3-1.7B", 1.7, 32768, 0.55, blocks=28),
            ModelProfile("Qwen3-3B", 3.0, 32768, 0.65, blocks=36),
        ),
    )
    edge = ResourceLayer(
        name="边缘", kind="edge", compute_tps=600.0, mem_gb=24.0,
        rtt_ms=12.0, cost_per_1k_tok=0.002,
        models=(ModelProfile("Qwen3-8B", 8.0, 32768, 0.78, blocks=36),),
    )
    cloud = ResourceLayer(
        name="云端", kind="cloud", compute_tps=2000.0, mem_gb=80.0,
        rtt_ms=60.0, cost_per_1k_tok=0.012,
        models=(
            ModelProfile("Qwen3-30B", 30.0, 131072, 0.92, blocks=48),
            ModelProfile("Mega-48B", 48.0, 131072, 0.95, blocks=48),
        ),
    )
    return ResourceEnvironment((end, edge, cloud))


class LocalSimExecutor(ExecutorPort):
    """mock #4 执行引擎：按资源画像模拟执行时延与成本（含轻微噪声）。"""

    def __init__(self, env: ResourceEnvironment, seed: int = 42):
        self.env = env
        self.rng = random.Random(seed)

    def execute(self, w: Subtask, d: ScheduleDecision) -> ExecutionResult:
        if not d.feasible:
            return ExecutionResult(False, 0.0, 0.0, 0, note="infeasible")
        real_lat = d.latency_ms * (0.9 + 0.2 * self.rng.random())
        return ExecutionResult(
            success=True, latency_ms=real_lat, cost=d.cost,
            tokens=w.tokens, note=d.reason or "ok",
        )


def _fmt_split(d: ScheduleDecision) -> str:
    if not d.split:
        return ""
    parts = [f"{name}:{b}" for name, b in d.split.block_allocation if b > 0]
    return f"  split[{d.split.mode}] " + " + ".join(parts)


def demo() -> None:
    env = default_env()
    executor = LocalSimExecutor(env)
    sched = Scheduler(env, executor)

    subtasks = [
        # 公开·超重·批处理 → 48B 单层放不下云端显存 → 端边云切分
        Subtask("w1", ComputeScale.S3_XHEAVY, LatencyTier.T3_BATCH,
                SensitivityLevel.L0_PUBLIC, est_input_tok=8000, est_output_tok=4000),
        # 机密·轻量·交互 → 仅端侧可承载
        Subtask("w2", ComputeScale.S0_LIGHT, LatencyTier.T0_INTERACTIVE,
                SensitivityLevel.L3_CONFIDENTIAL, est_input_tok=60, est_output_tok=20),
        # 内部·重型·分钟级 → 云端大模型
        Subtask("w3", ComputeScale.S2_HEAVY, LatencyTier.T2_MINUTE,
                SensitivityLevel.L1_INTERNAL, est_input_tok=5000, est_output_tok=2000),
        # 敏感·中等·分钟级 → 边缘模型
        Subtask("w4", ComputeScale.S1_MEDIUM, LatencyTier.T2_MINUTE,
                SensitivityLevel.L2_SENSITIVE, est_input_tok=1000, est_output_tok=500),
        # 机密·重型 → 端侧无法承载且不可切分 → 回送 #1 重规划
        Subtask("w5", ComputeScale.S2_HEAVY, LatencyTier.T2_MINUTE,
                SensitivityLevel.L3_CONFIDENTIAL, est_input_tok=4000, est_output_tok=2000),
    ]

    print("=" * 72)
    print("端-边-云自适应调度演示（单机模拟三层）")
    print("=" * 72)
    decisions: list[ScheduleDecision] = []
    for w in subtasks:
        d = sched.schedule(w)
        decisions.append(d)
        head = (f"[{w.id}] σ={w.sensitivity.name} s={w.scale.name} "
                f"τ={w.latency_tier.name} tok={w.tokens}")
        if d.feasible:
            print(f"{head}\n   → 层={d.layer_name} 模型={d.model_name} "
                  f"时延={d.latency_ms:.0f}ms 成本=¥{d.cost:.3f}{_fmt_split(d)}")
            res = executor.execute(w, d)
            print(f"     执行: {res}")
        else:
            print(f"{head}\n   ✗ 不可行: {d.reason}")

    print("-" * 72)
    total_cost = sum(d.cost for d in decisions if d.feasible)
    p_priv = privacy_satisfaction(decisions, subtasks, env)
    print(f"总资源开销 Cost_total = ¥{total_cost:.3f}")
    print(f"隐私约束满足率 P_priv = {p_priv:.2%}")


def demo_adaptive() -> None:
    """自适应调度演示：受限上下文 bandit 在线学习 + 事件日志。"""
    env = default_env()
    executor = LocalSimExecutor(env, seed=7)
    bandit = ContextualBandit(c=0.1, budget=10.0, sla_threshold=0.1)
    sched = AdaptiveScheduler(env, executor, bandit)
    logger = ScheduleLogger(path="scheduler_events.jsonl")

    # 任务流：重复同类任务以观察 bandit 探索→利用
    stream = (
        [("a", ComputeScale.S2_HEAVY, LatencyTier.T2_MINUTE,
          SensitivityLevel.L1_INTERNAL, 5000, 2000)] * 8
        + [("b", ComputeScale.S1_MEDIUM, LatencyTier.T2_MINUTE,
            SensitivityLevel.L2_SENSITIVE, 1000, 500)] * 4
        + [("c", ComputeScale.S3_XHEAVY, LatencyTier.T3_BATCH,
            SensitivityLevel.L0_PUBLIC, 8000, 4000)] * 2
        + [("d", ComputeScale.S2_HEAVY, LatencyTier.T2_MINUTE,
            SensitivityLevel.L3_CONFIDENTIAL, 4000, 2000)] * 2
    )

    print("=" * 72)
    print("自适应调度演示（受限上下文 bandit 在线学习）")
    print("=" * 72)
    seq_a: list[str] = []  # (S2,L1) 上下文的模型选择序列
    for step, (tag, sc, lt, sn, ti, to) in enumerate(stream):
        w = Subtask(f"{tag}{step}", sc, lt, sn, ti, to)
        d = sched.schedule(w)
        res = executor.execute(w, d)
        sched.feedback(w, d, res)
        logger.log(d, step)
        if (sc, sn) == (ComputeScale.S2_HEAVY, SensitivityLevel.L1_INTERNAL):
            seq_a.append(d.model_name if d.feasible else "—")

    print(f"(S2,L1) 模型选择序列: {seq_a}")
    print(f"(S2,L1) arm 分布: {bandit.arm_distribution((ComputeScale.S2_HEAVY, SensitivityLevel.L1_INTERNAL))}")
    print(f"(S1,L2) arm 分布: {bandit.arm_distribution((ComputeScale.S1_MEDIUM, SensitivityLevel.L2_SENSITIVE))}")
    logger.write_jsonl()
    print(f"事件日志已写入: {logger.path}")
    print("汇总:", logger.summary())


def demo_balance() -> None:
    """时间均衡演示（v0.3）：逐任务 vs 批量LPT 的 makespan/均衡度/空闲率 对比。"""
    env = default_env()
    executor = LocalSimExecutor(env)
    single = Scheduler(env, executor)
    batch = BatchScheduler(env, executor)

    tasks = [Subtask(f"t{i}", ComputeScale.S1_MEDIUM, LatencyTier.T2_MINUTE,
                     SensitivityLevel.L0_PUBLIC, 1000, 500) for i in range(9)]

    # 逐任务调度（每任务独立选最优 → 倾向全堆云端）
    st = LoadTracker([l.name for l in env.layers])
    for w in tasks:
        d = single.schedule(w)
        if d.feasible:
            st.assign(d.layer_name, d.latency_ms)

    # 批量调度（LPT 均衡）
    batch.schedule_batch(tasks)
    bt = batch.tracker

    print("=" * 72)
    print("时间均衡演示（v0.3：逐任务 vs 批量LPT）")
    print("=" * 72)
    print(f"{'指标':<14} {'逐任务':<18} {'批量LPT':<18} {'改善'}")
    print("-" * 72)
    ms_s, ms_b = makespan(st.loads()), makespan(bt.loads())
    bi_s, bi_b = load_balance_index(st.loads()), load_balance_index(bt.loads())
    ir_s, ir_b = idle_ratio(st.loads()), idle_ratio(bt.loads())
    print(f"{'makespan(ms)':<14} {ms_s:<18.0f} {ms_b:<18.0f} {(1 - ms_b / ms_s) * 100:+.1f}%")
    print(f"{'负载均衡度':<14} {bi_s:<18.3f} {bi_b:<18.3f} {(bi_b / bi_s - 1) * 100:+.1f}%")
    print(f"{'空闲率':<14} {ir_s:<18.3f} {ir_b:<18.3f} {(ir_b / ir_s - 1) * 100:+.1f}%")
    print(f"\n逐任务层负载: {st.loads()}")
    print(f"批量LPT层负载: {bt.loads()}")


def demo_dag() -> None:
    """DAG 运行时演示（v0.4）：菱形 DAG A→B→D / A→C→D 端到端执行。"""
    env = default_env()
    executor = LocalSimExecutor(env)
    rt = SchedulerRuntime(env, executor)

    dag = [
        Subtask("A", ComputeScale.S1_MEDIUM, LatencyTier.T2_MINUTE,
                SensitivityLevel.L0_PUBLIC, 1000, 500),
        Subtask("B", ComputeScale.S2_HEAVY, LatencyTier.T2_MINUTE,
                SensitivityLevel.L0_PUBLIC, 5000, 2000, depends_on=("A",)),
        Subtask("C", ComputeScale.S1_MEDIUM, LatencyTier.T2_MINUTE,
                SensitivityLevel.L0_PUBLIC, 1000, 500, depends_on=("A",)),
        Subtask("D", ComputeScale.S1_MEDIUM, LatencyTier.T2_MINUTE,
                SensitivityLevel.L0_PUBLIC, 1000, 500, depends_on=("B", "C")),
    ]

    print("=" * 72)
    print("DAG 运行时演示（v0.4：A→B→D / A→C→D 端到端）")
    print("=" * 72)
    result = rt.run(dag)
    for d in result["decisions"]:
        tag = "✗" if not d.feasible else f"→ {d.layer_name}/{d.model_name} {d.latency_ms:.0f}ms"
        split = f" [{d.split.mode}]" if d.split else ""
        print(f"  [{d.subtask_id}] {tag}{split}")
    print(f"\n关键路径: {result['critical_path']}")
    print(f"完成 {result['completed']}/{result['total']}，失败 {result['failed']}")
    print(f"汇总: {result['summary']}")


if __name__ == "__main__":
    demo()
    print()
    demo_adaptive()
    print()
    demo_balance()
    print()
    demo_dag()
