"""数据模型 — 资源层、模型、子任务、调度决策。
对齐《端边云调度模块设计.md》§6.1–6.3 的符号定义。"""
from __future__ import annotations
from dataclasses import dataclass
from enum import IntEnum
from typing import Optional


class SensitivityLevel(IntEnum):
    """数据敏感等级 σ_w（§6.2）。值越大越敏感。"""
    L0_PUBLIC = 0        # 公开：三层均可
    L1_INTERNAL = 1      # 内部：三层均可
    L2_SENSITIVE = 2     # 敏感：仅端/边，禁上云
    L3_CONFIDENTIAL = 3  # 机密：仅端侧


class ComputeScale(IntEnum):
    """计算规模 s_w 分级（§6.2）。"""
    S0_LIGHT = 0    # <2K tok·步
    S1_MEDIUM = 1   # 2–8K
    S2_HEAVY = 2    # 8–32K
    S3_XHEAVY = 3   # >32K


class LatencyTier(IntEnum):
    """实时性要求 τ_w 分级（§6.2）。"""
    T0_INTERACTIVE = 0  # <500ms
    T1_SECOND = 1       # 0.5–2s
    T2_MINUTE = 2       # 2–60s
    T3_BATCH = 3        # >60s


# 各计算规模所需的最小模型参数量（十亿）——能力筛选阈值
SCALE_MIN_PARAM_B = {
    ComputeScale.S0_LIGHT: 1.0,
    ComputeScale.S1_MEDIUM: 3.0,
    ComputeScale.S2_HEAVY: 8.0,
    ComputeScale.S3_XHEAVY: 35.0,
}

# 各实时性等级的时延预算上界（ms）
LATENCY_BUDGET_MS = {
    LatencyTier.T0_INTERACTIVE: 500.0,
    LatencyTier.T1_SECOND: 2_000.0,
    LatencyTier.T2_MINUTE: 60_000.0,
    LatencyTier.T3_BATCH: 600_000.0,
}

# 各敏感等级允许的资源层 kind（§6.2 隐私硬约束）
ALLOWED_LAYER_KINDS = {
    SensitivityLevel.L0_PUBLIC: ("end", "edge", "cloud"),
    SensitivityLevel.L1_INTERNAL: ("end", "edge", "cloud"),
    SensitivityLevel.L2_SENSITIVE: ("end", "edge"),
    SensitivityLevel.L3_CONFIDENTIAL: ("end",),
}


def allowed_layer_kinds(s: SensitivityLevel) -> tuple[str, ...]:
    """σ_w → 允许承载的层 kind 集合 L_w(σ_w)。"""
    return ALLOWED_LAYER_KINDS[s]


@dataclass(frozen=True)
class ModelProfile:
    """可部署模型 m = ⟨P, W, κ⟩（§6.1）。"""
    name: str
    param_b: float           # 参数量（十亿）
    context_window: int      # 上下文窗口（token）
    capability: float        # 能力画像 κ_m ∈ [0,1]
    blocks: int = 32         # transformer 层数（用于切分）

    @property
    def required_mem_gb(self) -> float:
        """fp16 显存占用估计（约 2×参数量）。"""
        return self.param_b * 2.0

    def can_handle(self, scale: ComputeScale) -> bool:
        """能力筛选：参数量是否达到该计算规模的最小要求。"""
        return self.param_b >= SCALE_MIN_PARAM_B[scale]

    def block_capacity(self, mem_gb: float) -> int:
        """给定显存可承载的最大块数。"""
        per_block = self.required_mem_gb / max(self.blocks, 1)
        return int(mem_gb / per_block) if per_block > 0 else self.blocks


@dataclass(frozen=True)
class ResourceLayer:
    """资源层 ℓ = ⟨C, M, δ, p, Φ⟩（§6.1）。"""
    name: str
    kind: str                  # 'end' | 'edge' | 'cloud'
    compute_tps: float         # C_ℓ：可用算力（tokens/s）
    mem_gb: float              # M_ℓ：显存/内存（GB）
    rtt_ms: float              # δ_ℓ：到任务源往返时延（ms）
    cost_per_1k_tok: float     # p_ℓ：单位成本（¥/1K tokens）
    models: tuple[ModelProfile, ...] = ()

    def find_model(self, name: str) -> Optional[ModelProfile]:
        for m in self.models:
            if m.name == name:
                return m
        return None


@dataclass(frozen=True)
class ResourceEnvironment:
    """三层资源环境（§6.1）。"""
    layers: tuple[ResourceLayer, ...]

    def by_name(self, name: str) -> Optional[ResourceLayer]:
        for l in self.layers:
            if l.name == name:
                return l
        return None

    def by_kind(self, kind: str) -> Optional[ResourceLayer]:
        for l in self.layers:
            if l.kind == kind:
                return l
        return None

    def kinds_by_name(self) -> dict[str, str]:
        return {l.name: l.kind for l in self.layers}


@dataclass(frozen=True)
class Subtask:
    """子任务 w，特征向量 f_w = (s_w, τ_w, σ_w)（§6.2）。"""
    id: str
    scale: ComputeScale
    latency_tier: LatencyTier
    sensitivity: SensitivityLevel
    est_input_tok: int = 1000
    est_output_tok: int = 1000
    depends_on: tuple[str, ...] = ()

    @property
    def latency_budget_ms(self) -> float:
        return LATENCY_BUDGET_MS[self.latency_tier]

    @property
    def tokens(self) -> int:
        return self.est_input_tok + self.est_output_tok


@dataclass(frozen=True)
class SplitPlan:
    """模型切分方案 π_w（§6.3.3）。"""
    mode: str  # 'layer' | 'phase' | 'none'
    block_allocation: tuple[tuple[str, int], ...] = ()  # (层名, 块数)
    phase_layers: Optional[tuple[str, str]] = None      # (prefill层, decode层)
    model_name: str = ""

    @property
    def is_split(self) -> bool:
        return self.mode != "none"


@dataclass(frozen=True)
class ScheduleDecision:
    """调度决策结果（§6.3）。"""
    subtask_id: str
    layer_name: str
    model_name: str
    split: Optional[SplitPlan] = None
    latency_ms: float = 0.0
    cost: float = 0.0
    feasible: bool = True
    reason: str = ""
