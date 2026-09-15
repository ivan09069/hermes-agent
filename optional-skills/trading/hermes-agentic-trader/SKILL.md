---
name: hermes-agentic-trader
description: Paper-safe Base/EVM market analysis using a restricted defi-trading MCP surface.
version: 0.7.0-repair.2
author: ivan09069
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Trading, DeFi, Base, EVM, MCP]
    related_skills: []
---

# Hermes Agentic Trader — Repair Track

This repair track is intentionally market-data-only. Live writes remain blocked
by the bundled hermes-agentic-trader plugin.

## Required setup

1. Install the curated defi-trading MCP catalog entry.
2. Enable the safety plugin with: hermes plugins enable hermes-agentic-trader
3. Keep trader.mode set to paper in ~/.hermes/config.yaml.

The default repair surface requires only a CoinGecko API key. It does not
require a wallet address or private key.

## Security boundary

The exact pinned package, defi-trading-mcp@2.1.3, routes its aggregator-backed
portfolio, swap quote, gasless, and execution features through an external
plaintext HTTP endpoint. Those tools are intentionally excluded from the
manifest's default include list.

Do not manually enable execute_swap, submit_gasless_swap, get_swap_quote,
get_gasless_quote, or the aggregator-backed portfolio tools for this repair
track. The plugin still blocks raw write calls as defense in depth.

## Base market scan

For Base trending pools call get_trending_pools_by_network with:

- network: base
- include: base_token,quote_token,dex
- duration: 24h

Do not substitute global get_trending_pools and then label its results as Base.
Do not use global get_new_pools as a Base-only source.

CoinGecko/GeckoTerminal pool data distinguishes:

- the pool contract address in data.attributes.address;
- the base token through data.relationships.base_token;
- the quote token through data.relationships.quote_token.

The pool contract is never the token-to-buy address. Resolve the token
relationship to the corresponding included token object, or its resource ID,
before producing a recommendation.

## Output

Report the network, pool address, base token symbol and contract, quote token
symbol and contract, liquidity, 24h volume, 24h price change, and an analysis
recommendation.

End with: PAPER MODE — no transaction submitted.

## Live execution

Live execution is not part of this repair-track surface. The quote-binding,
signed-mandate, and deterministic risk modules are retained as fail-closed
defense-in-depth and future migration work, but no transaction path is enabled.
