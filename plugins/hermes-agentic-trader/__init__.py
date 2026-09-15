"""Hermes Agentic Trader safety boundary.

This repair plugin intentionally keeps live swap execution quarantined while
PR #60159 is ported to current Hermes. Read/quote tools remain available, but
raw write tools fail closed before dispatch.

The policy lives at Hermes' supported pre_tool_call hook boundary rather than
patching MCP transport internals.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Mapping, Optional

LIVE_WRITE_TOOLS = frozenset({"execute_swap", "submit_gasless_swap"})
_TRUTHY = frozenset({"1", "true", "yes", "on"})


def _load_trader_config() -> Mapping[str, Any]:
    """Return the trader config mapping; malformed/unavailable config fails safe."""
    try:
        from hermes_cli.config import load_config

        config = load_config() or {}
    except Exception:
        return {}
    if not isinstance(config, dict):
        return {}
    trader = config.get("trader") or {}
    return trader if isinstance(trader, dict) else {}


def _kill_switch_active() -> bool:
    """Honor both the environment and the on-disk emergency stop."""
    if os.environ.get("HERMES_TRADER_KILL_SWITCH", "").strip().lower() in _TRUTHY:
        return True
    try:
        from hermes_constants import get_hermes_home

        return (Path(get_hermes_home()) / "trader" / "KILL_SWITCH").is_file()
    except Exception:
        return False


def _block(message: str) -> dict[str, str]:
    return {"action": "block", "message": message}


def _on_pre_tool_call(
    tool_name: str = "",
    args: Optional[dict[str, Any]] = None,
    **_: Any,
) -> Optional[dict[str, str]]:
    """Fail closed for live swap tools until the repaired quote-bound gate lands."""
    del args

    if tool_name not in LIVE_WRITE_TOOLS:
        return None

    if _kill_switch_active():
        return _block(
            "Hermes Agentic Trader blocked this write: the trader kill switch is active."
        )

    trader = _load_trader_config()
    mode = str(trader.get("mode", "paper")).strip().lower()

    if mode != "live":
        return _block(
            "Hermes Agentic Trader is in paper mode. Live MCP write tools are blocked."
        )

    # Deliberate quarantine. PR #60159 previously validated a synthetic argument
    # shape that does not match defi-trading-mcp@2.1.3's quoteData contract.
    # Do not allow raw writes until quote-bound validation, portfolio/P&L context,
    # and execution reconciliation have been ported and tested on current Hermes.
    return _block(
        "Hermes Agentic Trader live execution is quarantined on the PR #60159 "
        "repair branch. Raw execute_swap/submit_gasless_swap calls are disabled "
        "until the quote-bound risk gate and exact MCP contract tests are complete."
    )


def register(ctx) -> None:
    """Register the fail-closed policy hook with current Hermes."""
    ctx.register_hook("pre_tool_call", _on_pre_tool_call)
