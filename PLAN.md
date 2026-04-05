# Gassavant Phase Plan

## Vision
Transform Gassavant from a basic gas oracle into the **Go/No-Go Brain** for autonomous agent execution.

---

## Phase 1: Gassavant Gas Oracle
**Status:** 🚀 API Built — Ready for x402 Integration
**Goal:** Deliver predictive gas + congestion analysis so agents optimize transaction timing.

1.  **Data Ingestion** ✅
    - [x] Wire up live Etherscan/Alchemy RPC calls for real-time base fee + priority fee data.
    - [x] `GET /v1/gas/current` — live gas prices (Fuji + Ethereum mainnet)
    - [x] Historical data fetching for Prophet model retraining

2.  **API Implementation** ✅
    - [x] Full rewrite of `api/main.py` — live data + Prophet inference + heuristic fallback
    - [x] `GET /v1/gas/forecast` — 15m/1h prediction + EXECUTE/WAIT signal
    - [x] `POST /v1/gas/optimize` — agent decision endpoint with savings estimation
    - [x] Agent-native discovery: `/.well-known/llm.txt`, `/mcp` (tool definitions)

3.  **Composed Protocol Integration**
    - [ ] Deploy endpoint on the existing x402 Server (replace `/weather-2`)
    - [ ] Register endpoint on-chain via CLI (`register-endpoint`)
    - [ ] Automate `distribute()` and harvest routing to maintain YT yield

---

## Phase 2: Smart Execution Router
**Status:** Planned
**Goal:** Provide cross-chain routing intelligence + execution payloads.

1.  **CCIP Integration**
    - [ ] Integrate `ccip-terminal-ts` logic into the backend.
    - [ ] Add endpoint `GET /v1/route/optimal?src=&dst=&asset=`.
    - [ ] Compare costs across L2s (Arbitrum vs Base vs OP) including bridge fees.

2.  **Agent-Native Outputs**
    - [ ] Return encoded calldata ready for agent signing.
    - [ ] Implement "Total Execution Cost" metric (Gas + Bridge + Protocol Fee).

---

## Phase 3: Credit & Risk Layer
**Status:** Future
**Goal:** Enable Agent Treasury Management via solvency and behavioral scoring.

1.  **Treasury Intelligence**
    - [ ] Build `GET /v1/treasury/health` (Runway prediction, token concentration).
    - [ ] Build `GET /v1/credit/score` (Counterparty risk analysis).

2.  **ML Expansion**
    - [ ] Train new models on DAO treasury outflows and protocol revenue streams.
    - [ ] Add anomaly detection for rug-pull/fraud patterns.

---

## Phase 4: Unified Composed Protocol CLI (Agent-Native)
**Status:** 🚀 High Priority
**Goal:** Unified TypeScript CLI (`composed-skill`) handles full lifecycle — deployment to asset management.

1.  **Admin / Deployment (Python CLI parity)**
    - [ ] `deploy-provider` — Deploy RS token + splitter, register in registry
    - [ ] `register-endpoint` — Fetch x402 hash from live server + register on-chain
    - [ ] `update-endpoint` — Update integrity hash after price changes
    - [ ] `update-provider` — Update metadata URI, payout, or splitter

2.  **Staking & Treasury**
    - [ ] `stake` — Ensure account meets minimum stake requirement
    - [ ] `unstake` — Request unstake (starts cooldown)
    - [ ] `withdraw` — Withdraw after cooldown expires

3.  **Integrity & Security**
    - [ ] `verify-contract` — Verify contract source on SnowScan
    - [ ] `challenge` — Open CRE integrity challenge for an endpoint
    - [ ] `challenge-status` — Check the result of a challenge

4.  **Inspection (JSON / MCP Ready)**
    - [ ] `status` — Signer, stake, USDC balance + all deployed provider stats
    - [ ] `registry` — List all providers and their endpoints
    - [ ] `splitter` — Pending balance, routing config; optionally distribute
    - [ ] `revenue-share` — RS supply, EPS, claimable USDC

5.  **L2 Asset Management (Existing)**
    - [ ] `deposit` — Mint PT/YT from RS
    - [ ] `harvest` — Yield harvesting + routing
    - [ ] `claim-yt` — Claim USDC dividends
    - [ ] `redeem-pt` — Redeem matured PT for underlying RS

## Infrastructure
- **Repo:** `/root/gassavant` (API) + `/root/composed-protocol-private` (Protocol)
- **API:** FastAPI (`api/main.py`)
- **ML:** Prophet (`AI/prophet_model.pkl`)
- **Payment:** Composed Protocol (x402 -> Splitter -> RS -> PT/YT)
- **CLI:** `/root/composed-protocol-private/cli/composed-skills` (TypeScript + viem)
