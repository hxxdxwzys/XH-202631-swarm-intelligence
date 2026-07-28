"""模型切分点选择（§6.3.3）— EdgeShard 式层切分。
v0.1 用枚举求最优块分配（层数 ≤3、块数 ~48，枚举量小，C(K+n-1,n-1) 量级）。
v0.2 再引入阶段切分（prefill/decode 解耦）与 DP 加速。"""
from __future__ import annotations
from core.scheduler.models import (
    ModelProfile, Subtask, ResourceEnvironment, SplitPlan,
)
from core.scheduler.metrics import latency_layer_split


def _allocations(k: int, n: int):
    """生成 n 维非负整数分配，sum == k。"""
    if n == 1:
        yield (k,)
        return
    for b in range(k + 1):
        for rest in _allocations(k - b, n - 1):
            yield (b,) + rest


def best_layer_split(w: Subtask, model: ModelProfile, env: ResourceEnvironment,
                     allowed_kinds: tuple[str, ...]) -> SplitPlan | None:
    """在允许层中选择块分配，最小化层切分时延（受各层显存容量约束）。

    返回最优 SplitPlan；若无有效分配（如总容量不足或层数 <2）返回 None。
    """
    layers = [env.by_kind(k) for k in allowed_kinds]
    layers = [l for l in layers if l is not None]
    if len(layers) < 2:
        return None

    K = model.blocks
    caps = [model.block_capacity(l.mem_gb) for l in layers]
    if sum(caps) < K:
        return None  # 即便切分，总显存也不够

    n = len(layers)
    best_plan: SplitPlan | None = None
    best_lat = float("inf")
    for alloc in _allocations(K, n):
        # 容量约束 + 至少两层参与
        if any(alloc[i] > caps[i] for i in range(n)):
            continue
        if sum(1 for b in alloc if b > 0) < 2:
            continue
        block_allocation = tuple((layers[i].name, alloc[i]) for i in range(n))
        plan = SplitPlan(mode="layer", block_allocation=block_allocation,
                         model_name=model.name)
        lat = latency_layer_split(w, plan, env)
        if lat < best_lat:
            best_lat = lat
            best_plan = plan
    return best_plan
