from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load_policy():
    spec = importlib.util.spec_from_file_location(
        "standalone_policy",
        ROOT / "policy.py",
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_live_defaults_to_canary():
    policy = load_policy()
    cfg = policy.TraderPolicy.from_mapping({"mode": "live"})
    assert cfg.rollout_stage == "canary"
    assert cfg.allowed_chain_ids == (8453,)
    assert cfg.rollout_cap_usd == 50.0


def test_paper_defaults_to_zero_cap():
    policy = load_policy()
    cfg = policy.TraderPolicy.from_mapping({"mode": "paper"})
    assert cfg.rollout_stage == "paper"
    assert cfg.rollout_cap_usd == 0.0
