from __future__ import annotations

import importlib.util
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_module(name: str):
    package = "hermes_agentic_trader_testpkg"
    if package not in sys.modules:
        pkg = types.ModuleType(package)
        pkg.__path__ = [str(ROOT)]
        sys.modules[package] = pkg
    full = f"{package}.{name}"
    spec = importlib.util.spec_from_file_location(full, ROOT / f"{name}.py")
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {name}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[full] = mod
    spec.loader.exec_module(mod)
    return mod


def test_policy() -> None:
    policy = load_module("policy")

    live = policy.TraderPolicy.from_mapping({"mode": "live"})
    assert live.rollout_stage == "canary"
    assert live.allowed_chain_ids == (8453,)
    assert live.rollout_cap_usd == 50.0

    paper = policy.TraderPolicy.from_mapping({"mode": "paper"})
    assert paper.rollout_stage == "paper"
    assert paper.rollout_cap_usd == 0.0


def test_uniswap() -> None:
    u = load_module("uniswap_v3")
    u.clear_direct_quotes()

    token_in = "0x1111111111111111111111111111111111111111"
    token_out = "0x2222222222222222222222222222222222222222"
    owner = "0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"

    assert u.BASE_CHAIN_ID == 8453
    assert u.BASE_CHAIN_HEX == "0x2105"
    assert u.SWAP_ROUTER_02 == "0x2626664c2603336e57b271c5c0b26f421741e481"
    assert u.QUOTER_V2 == "0x3d4e44eb1374240ce5f1b871ab261cd16335b76a"

    calldata = u.quote_calldata(
        token_in=token_in,
        token_out=token_out,
        amount_in=1_000_000,
        fee=500,
    )
    assert calldata.startswith("0xc6a5026a")
    assert len(calldata) == 2 + 8 + 64 * 5

    record = u.DirectQuote(
        quote_id="q1",
        session_id="s1",
        token_in=token_in,
        token_out=token_out,
        amount_in=1_000_000,
        fee=500,
        amount_out=2_000_000,
        sqrt_price_x96_after=12345,
        initialized_ticks_crossed=7,
        gas_estimate=180000,
        captured_at=10.0,
    )
    payload = u.build_wallet_send_calls(
        owner=owner,
        quote=record,
        slippage_bps=50,
    )
    request = payload["params"][0]
    assert payload["method"] == "wallet_sendCalls"
    assert request["version"] == "2.0.0"
    assert request["chainId"] == "0x2105"
    assert request["atomicRequired"] is True
    assert request["from"] == owner

    approval, swap = request["calls"]
    assert approval["to"] == token_in
    assert approval["data"].startswith("0x095ea7b3")
    assert swap["to"] == u.SWAP_ROUTER_02
    assert swap["data"].startswith("0x04e45aaf")
    assert payload["quote"]["amount_out_minimum"] == "1990000"

    original = u.rpc_call
    try:
        u.rpc_call = lambda *args, **kwargs: "0x1"
        try:
            u.fetch_direct_quote(
                token_in=token_in,
                token_out=token_out,
                amount_in=1_000_000,
                fee=500,
                session_id="s1",
            )
        except RuntimeError as exc:
            assert "not Base mainnet" in str(exc)
        else:
            raise AssertionError("wrong-chain quote was not rejected")
    finally:
        u.rpc_call = original


if __name__ == "__main__":
    test_policy()
    test_uniswap()
    print("PASS: standalone pure-module tests")
