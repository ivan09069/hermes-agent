from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]


def load_module(name: str):
    package = "hermes_agentic_trader"
    if package not in sys.modules:
        import types

        pkg = types.ModuleType(package)
        pkg.__path__ = [str(ROOT)]
        sys.modules[package] = pkg
    full = f"{package}.{name}"
    spec = importlib.util.spec_from_file_location(full, ROOT / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[full] = mod
    spec.loader.exec_module(mod)
    return mod


TOKEN_IN = "0x1111111111111111111111111111111111111111"
TOKEN_OUT = "0x2222222222222222222222222222222222222222"
OWNER = "0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"


@pytest.fixture
def u():
    module = load_module("uniswap_v3")
    module.clear_direct_quotes()
    return module


def test_pinned_base_deployments(u):
    assert u.BASE_CHAIN_ID == 8453
    assert u.BASE_CHAIN_HEX == "0x2105"
    assert u.SWAP_ROUTER_02 == "0x2626664c2603336e57b271c5c0b26f421741e481"
    assert u.QUOTER_V2 == "0x3d4e44eb1374240ce5f1b871ab261cd16335b76a"


def test_quote_calldata_is_local(u):
    data = u.quote_calldata(
        token_in=TOKEN_IN,
        token_out=TOKEN_OUT,
        amount_in=1_000_000,
        fee=500,
    )
    assert data.startswith("0xc6a5026a")
    assert len(data) == 2 + 8 + 64 * 5


def test_wallet_bundle_is_unsigned_and_atomic(u):
    record = u.DirectQuote(
        quote_id="q1",
        session_id="s1",
        token_in=TOKEN_IN,
        token_out=TOKEN_OUT,
        amount_in=1_000_000,
        fee=500,
        amount_out=2_000_000,
        sqrt_price_x96_after=12345,
        initialized_ticks_crossed=7,
        gas_estimate=180000,
        captured_at=10.0,
    )
    payload = u.build_wallet_send_calls(
        owner=OWNER,
        quote=record,
        slippage_bps=50,
    )
    request = payload["params"][0]
    assert payload["method"] == "wallet_sendCalls"
    assert request["version"] == "2.0.0"
    assert request["chainId"] == "0x2105"
    assert request["atomicRequired"] is True
    assert request["from"] == OWNER

    approval, swap = request["calls"]
    assert approval["to"] == TOKEN_IN
    assert approval["data"].startswith("0x095ea7b3")
    assert swap["to"] == u.SWAP_ROUTER_02
    assert swap["data"].startswith("0x04e45aaf")
    assert payload["quote"]["amount_out_minimum"] == "1990000"


def test_wrong_chain_quote_is_rejected(u, monkeypatch):
    monkeypatch.setattr(u, "rpc_call", lambda *a, **k: "0x1")
    with pytest.raises(RuntimeError, match="not Base mainnet"):
        u.fetch_direct_quote(
            token_in=TOKEN_IN,
            token_out=TOKEN_OUT,
            amount_in=1_000_000,
            fee=500,
            session_id="s1",
        )
