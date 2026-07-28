"""配置化资源环境（§6.1）—— 从 dict/JSON 加载，便于团队标定实际算力而不改代码。"""
from __future__ import annotations
import json
from core.scheduler.models import ResourceEnvironment, ResourceLayer, ModelProfile


def env_from_dict(d: dict) -> ResourceEnvironment:
    """d = {"layers": [{"name","kind","compute_tps","mem_gb","rtt_ms","cost_per_1k_tok","models":[{...}]}]}"""
    layers = []
    for ld in d["layers"]:
        models = tuple(ModelProfile(**md) for md in ld.get("models", []))
        layers.append(ResourceLayer(
            name=ld["name"], kind=ld["kind"],
            compute_tps=ld["compute_tps"], mem_gb=ld["mem_gb"],
            rtt_ms=ld["rtt_ms"], cost_per_1k_tok=ld["cost_per_1k_tok"],
            models=models,
        ))
    return ResourceEnvironment(tuple(layers))


def load_env(path: str) -> ResourceEnvironment:
    with open(path, encoding="utf-8") as f:
        return env_from_dict(json.load(f))
