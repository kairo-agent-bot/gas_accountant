# Gassavant: Agent Gas Oracle

Gassavant is an x402-gated API designed for autonomous agents operating on EVM chains. It provides real-time gas prices, predictive forecasting, and transaction optimization to maximize agent profitability.

## Agent-Centric Endpoints

### 1. `GET /v1/gas/forecast`
*   **x402 Price:** $0.01 (10,000 USDC units)
*   **Query:** `?chain_id=1` (Integer ID, e.g., 1 for Mainnet, 43113 for Fuji)
*   **What it does:** Fetches live gas data, runs it through a heuristic model (Mean Reversion), and returns a 15-minute / 1-hour prediction.
*   **Agent Use Case (The Scheduler):**
    An agent programmed to rebalance a portfolio at 2:00 PM calls this at 1:55 PM. If the signal is `"WAIT"`, the agent delays execution by 45 minutes to save potentially 20% on fees.

### 2. `GET /v1/gas/current`
*   **x402 Price:** $0.005 (5,000 USDC units)
*   **Query:** `?chain_id=43114`
*   **What it does:** Returns the precise market price (Safe/Propose/Fast) for a specific chain right now.
*   **Agent Use Case (The Quoter):**
    A bridge aggregator agent uses this to calculate the exact fee impact on a user's wallet before executing a cross-chain swap. This allows for "Total Cost" comparisons across multiple chains (e.g., Base vs. Arbitrum).

### 3. `POST /v1/gas/optimize`
*   **x402 Price:** $0.01 (10,000 USDC units)
*   **Payload:** `{"chain_id": 1, "max_gas_gwei": 50}`
*   **What it does:** Simulates the transaction economics against your constraints. It tells you if the current conditions meet your profitability threshold.
*   **Agent Use Case (The Risk Manager):**
    An "Arb Bot" spots a $5 profit opportunity. It calls this endpoint. If the forecast says gas will spike to a level where the cost is $7, the bot realizes the trade will net -$2 and kills the trade automatically.

## Why Agents Pay for This
*   **Profit Maximization:** Agents with "skin in the game" (owning their own USDC) lose money if they overpay for gas. This API acts as a rational filter to prevent wasted capital.
*   **Mempool Survival:** On L2s like Base/Arbitrum, gas spikes can trap transactions in the mempool. Predictive forecasts prevent agents from bidding too low and failing their own transactions.
