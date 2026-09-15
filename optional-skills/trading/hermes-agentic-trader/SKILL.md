---
name: hermes-agentic-trader
description: Paper-safe Base/EVM market analysis using the pinned defi-trading MCP integration.
version: 0.7.0-repair.1
author: ivan09069
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Trading, DeFi, Base, EVM, MCP]
    related_skills: []
---

# Hermes Agentic Trader — Repair Track

This skill is intentionally paper-safe while PR #60159 is being repaired for
current Hermes. Live write tools remain blocked by the bundled
hermes-agentic-trader plugin.

## Required setup

1. Install/configure the defi-trading MCP catalog entry.
2. Enable the safety plugin with: hermes plugins enable hermes-agentic-trader
3. Keep trader.mode set to paper in ~/.hermes/config.yaml.

A private key is not required for paper analysis.

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
before producing a trade recommendation.

## Output

Report the network, pool address, base token symbol and contract, quote token
symbol and contract, liquidity, 24h volume, 24h price change, and an analysis
recommendation.

End with: PAPER MODE — no transaction submitted.

## Live execution

execute_swap and submit_gasless_swap are quarantined on the repair track.
Do not instruct the user to bypass the plugin gate. Live execution will only
be enabled after quote binding, mandate validation, notional/portfolio/P&L
limits, and execution reconciliation are all covered by tests.
