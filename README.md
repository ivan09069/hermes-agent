# Hermes Agentic Trader

Standalone Hermes plugin for **Base mainnet Uniswap V3 quoting** and **unsigned EIP-5792 transaction planning**.

This repository is the standalone form of the repaired trader work that superseded NousResearch/hermes-agent#60159.

## Security model

- No private key is accepted or stored.
- No transaction is signed or submitted.
- Quotes are read directly from Base with `eth_call` against the pinned official Uniswap QuoterV2 deployment.
- Transaction calldata is constructed locally.
- The output is an **unsigned** `wallet_sendCalls` request for an external wallet to simulate and approve.
- The wallet request sets `atomicRequired: true`.
- Only ERC-20 -> ERC-20, single-pool Uniswap V3 swaps on Base are supported.
- Arbitrary routers, native ETH wrapping, Permit2 signatures, multi-hop routing, and automatic submission are intentionally out of scope.

## Install

Hermes supports standalone Git plugins:

```bash
hermes plugins install ivan09069/hermes-agentic-trader --no-enable
hermes plugins enable hermes-agentic-trader
```

For a private repository, authenticate GitHub first with `gh auth login` or provide a GitHub token through Hermes' supported credential flow.

For reproducible installs, pin a full commit:

```bash
hermes plugins install ivan09069/hermes-agentic-trader --ref <full-40-character-commit>
```

## Tools

### `trader_uniswap_quote`

Read-only direct quote on Base.

Inputs:

- `token_in`: ERC-20 address
- `token_out`: ERC-20 address
- `amount_in`: decimal string in base units
- `fee`: one of `100`, `500`, `3000`, `10000`

The tool verifies the RPC chain ID is Base (`8453`) before quoting.

### `trader_uniswap_build_calls`

Builds, but does **not submit**, an unsigned EIP-5792 request from a fresh quote.

Inputs:

- `quote_id`: fresh quote returned by `trader_uniswap_quote`
- `owner`: wallet address
- `slippage_bps`: requested slippage tolerance

Output includes:

- `wallet_getCapabilities` preflight
- `wallet_sendCalls` v2.0.0 request
- exact-amount ERC-20 approval
- Uniswap `exactInputSingle` swap call
- locally computed `amountOutMinimum`
- `atomicRequired: true`

Always inspect the wallet simulation before signing.

## Configuration

Optional Hermes trader policy in `~/.hermes/config.yaml`:

```yaml
trader:
  mode: paper
  rollout_stage: paper
  allowed_chains:
    - base
  max_slippage_bps: 100
  max_position_pct: 5
  max_daily_loss_pct: 3
  max_write_tools_per_hour: 10
```

The standalone plugin currently uses `max_slippage_bps` when constructing unsigned calls. It does not submit transactions, so live capital controls remain advisory until a separately reviewed wallet-execution bridge exists.

## RPC

Default read-only RPC:

```text
https://mainnet.base.org
```

Override with:

```bash
EVM_RPC_URL=https://your-base-rpc.example
```

The plugin rejects the RPC if `eth_chainId` is not Base mainnet.

## Pinned Uniswap deployments

Deployment source:

- repository: `Uniswap/contracts`
- commit: `e34ba78b05663c8c342cce69b0039067ace75691`
- Base SwapRouter02: `0x2626664c2603336e57b271c5c0b26f421741e481`
- Base QuoterV2: `0x3d4e44eb1374240ce5f1b871ab261cd16335b76a`

## Origin

The original in-tree proposal was reworked after review identified that the earlier `defi-trading-mcp@2.1.3` execution path depended on an external plaintext-HTTP aggregator. This standalone plugin does not use that execution backend.

## License

MIT.
