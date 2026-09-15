"""Hermes Agentic Trader standalone plugin."""

from __future__ import annotations

from . import tools as _tools


def register(ctx) -> None:
    """Register safe direct-quote and unsigned-wallet-planning tools."""
    ctx.register_tool(
        name="trader_uniswap_quote",
        toolset="trader",
        schema=_tools.TRADER_UNISWAP_QUOTE_SCHEMA,
        handler=_tools.handle_uniswap_quote,
        emoji="📈",
    )
    ctx.register_tool(
        name="trader_uniswap_build_calls",
        toolset="trader",
        schema=_tools.TRADER_UNISWAP_BUILD_CALLS_SCHEMA,
        handler=_tools.handle_uniswap_build_calls,
        emoji="🧾",
    )
