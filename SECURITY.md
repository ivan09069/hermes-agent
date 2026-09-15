# Security

Hermes Agentic Trader is intentionally non-custodial.

## Guarantees

- The plugin does not accept a raw private key.
- The plugin does not sign transactions.
- The plugin does not submit transactions.
- The plugin rejects non-Base RPC endpoints by checking `eth_chainId`.
- Router and quoter addresses are pinned from an immutable Uniswap deployment source commit.
- Quote IDs expire and bind unsigned planning to a previously observed quote.
- Wallet execution must happen outside Hermes after wallet simulation and human approval.

## Scope

Supported:
- Base mainnet
- ERC-20 to ERC-20
- Uniswap V3 single-pool `exactInputSingle`
- EIP-5792 unsigned call planning

Not supported:
- arbitrary routers
- native ETH wrapping
- multi-hop routing
- Permit2 signatures
- private-key custody
- automatic transaction submission

Do not bypass these boundaries without a separate security review.
