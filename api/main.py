import os
import json
import base64
import time
import aiohttp
import numpy as np
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, Request, Query
from fastapi.responses import JSONResponse
from starlette.middleware.cors import CORSMiddleware

# ── Config ──────────────────────────────────────────────────────────────
ASSET = "0x5425890298aed601595a70AB815c96711a31Bc65"
PAY_TO = "0x4E58B251cd6421F53D25f814afA145548E7e6A2F"
NETWORK = "eip155:43113"
PRICING = {
    "/v1/gas/forecast": "10000",    # $0.01
    "/v1/gas/current": "5000",     # $0.005
    "/v1/gas/optimize": "10000"    # $0.01
}

# Chain ID Mapping
# Key: Chain ID, Value: Source/Config
CHAIN_MAP = {
    1: {"name": "Ethereum Mainnet", "source": "etherscan"},
    43113: {"name": "Avalanche Fuji (Testnet)", "source": "rpc", "rpc": "https://api.avax-test.network/ext/bc/C/rpc"},
    43114: {"name": "Avalanche C-Chain", "source": "rpc", "rpc": "https://api.avax.network/ext/bc/C/rpc"}
}

ETHERSCAN_API_KEY = os.getenv("ETHERSCAN_API_KEY", "")

app = FastAPI(title="Gassavant Gas Oracle", version="1.0.0 (Unified)")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# ── x402 Middleware ─────────────────────────────────────────────────────
async def build_402(req_url, path):
    amount = PRICING.get(path, "10000")
    desc = "Gassavant Oracle API"
    if "forecast" in path: desc = "Forecast gas prices + EXECUTE/WAIT signal"
    elif "current" in path: desc = "Live gas prices"
    
    config = {
        "x402Version": 2,
        "error": "Payment required",
        "resource": {"url": req_url, "description": desc, "mimeType": "application/json"},
        "accepts": [{
            "scheme": "exact", 
            "network": NETWORK, 
            "amount": amount, 
            "asset": ASSET, 
            "payTo": PAY_TO, 
            "extra": {"name": "USD Coin", "version": "2"}
        }]
    }
    payload = base64.b64encode(json.dumps(config).encode()).decode()
    return JSONResponse(
        status_code=402, 
        content={"error": "Payment Required"}, 
        headers={"PAYMENT-REQUIRED": payload}
    )

@app.middleware("http")
async def toll_booth(request: Request, call_next):
    path = request.url.path
    
    # Allow free endpoints
    if path.startswith("/docs") or path.startswith("/openapi") or path.startswith("/redoc") or path.startswith("/mcp") or path.startswith("/.well-known") or path == "/":
        return await call_next(request)

    # Check if route requires payment
    if path.startswith("/v1/gas"):
        pay_header = request.headers.get("x-x402-payment") or request.headers.get("x-payment")
        
        if not pay_header:
            return await build_402(str(request.url), path)
        
    return await call_next(request)

# ── Data Ingestion ──────────────────────────────────────────────────────
async def fetch_gas_rpc(rpc_url: str):
    """Fetch gas price from a raw RPC endpoint."""
    try:
        async with aiohttp.ClientSession() as s:
            payload = {"jsonrpc": "2.0", "method": "eth_gasPrice", "params": [], "id": 1}
            async with s.post(rpc_url, json=payload, timeout=10) as r:
                gas = int((await r.json())["result"], 16)
                return {"base_fee_gwei": round(gas / 1e9, 2)}
    except: 
        return {"base_fee_gwei": 0.0}

async def fetch_eth_gas():
    """Fetch live Ethereum mainnet gas from Etherscan."""
    if not ETHERSCAN_API_KEY: return {"safe_low": 30, "propose": 35, "fast": 40}
    try:
        async with aiohttp.ClientSession() as s:
            url = f"https://api.etherscan.io/api?module=gastracker&action=gasoracle&apikey={ETHERSCAN_API_KEY}"
            async with s.get(url, timeout=10) as r:
                res = (await r.json())["result"]
                return {
                    "safe_low": float(res.get("SafeGasPrice", 30)), 
                    "propose": float(res.get("ProposeGasPrice", 35)), 
                    "fast": float(res.get("FastGasPrice", 40))
                }
    except: 
        return {"safe_low": 30, "propose": 35, "fast": 40}

def forecast(current_gwei):
    """Heuristic forecast (Mean Reversion)."""
    trend = np.random.normal(0, 1)
    mean = 30.0
    p15 = max(current_gwei * 0.7 + mean * 0.3 + trend, 0.5)
    p1h = max(current_gwei * 0.4 + mean * 0.6 + trend * 1.5, 0.5)
    return {"prediction_15m": round(p15, 2), "prediction_1h": round(p1h, 2)}

def generate_signal(current, p15, p1h):
    if current <= p15 * 0.9: return {"signal": "EXECUTE", "reason": "Price below near-term forecast"}
    if current >= p1h * 1.2: return {"signal": "WAIT", "reason": "Price significantly above forecast"}
    return {"signal": "EXECUTE", "reason": "Price within normal volatility"}

# ── Endpoints ──────────────────────────────────────────────────────────────
@app.get("/")
async def root():
    return {"status": "active", "service": "Gassavant Gas Oracle v1.0.0 (Unified)", "supported_chains": list(CHAIN_MAP.keys())}

@app.get("/.well-known/llm.txt")
async def llm_txt():
    return "# Gassavant Gas Oracle\n\nAI agents: use these x402-gated endpoints:\n- GET /v1/gas/forecast?chain_id=1 → EXECUTE/WAIT decision\n- GET /v1/gas/current?chain_id=43113 → Live gas prices\n- GET /mcp → Tool definitions for MCP clients\nAll prices in Gwei. Payments via x402 on Fuji (eip155:43113).\n"

@app.get("/mcp")
async def mcp_tools():
    return {"tools": [
        {"name": "gas_forecast", "description": "Forecast gas prices 15m/1h ahead with EXECUTE/WAIT signal", "inputSchema": {"type": "object", "properties": {"chain_id": {"type": "integer", "default": 1}}}},
        {"name": "gas_current", "description": "Get current live gas prices", "inputSchema": {"type": "object", "properties": {"chain_id": {"type": "integer", "default": 1}}}}
    ]}

@app.get("/v1/gas/current")
async def get_current(chain_id: int = Query(1, description="Ethereum Chain ID (e.g., 1, 43113)")):
    meta = CHAIN_MAP.get(chain_id) or CHAIN_MAP[1]
    if meta["source"] == "rpc":
        return {"chain_id": chain_id, "network": meta["name"], "data": await fetch_gas_rpc(meta["rpc"])}
    return {"chain_id": chain_id, "network": meta["name"], "data": await fetch_eth_gas()}

@app.get("/v1/gas/forecast")
async def get_forecast(chain_id: int = Query(1, description="Ethereum Chain ID (e.g., 1, 43113)")):
    meta = CHAIN_MAP.get(chain_id) or CHAIN_MAP[1]
    
    if meta["source"] == "rpc":
        data = await fetch_gas_rpc(meta["rpc"])
        current = data.get("base_fee_gwei", 25)
    else:
        data = await fetch_eth_gas()
        current = data.get("propose", 35)
        
    fc = forecast(current)
    sig = generate_signal(current, fc["prediction_15m"], fc["prediction_1h"])
    
    return {
        "chain_id": chain_id, 
        "network": meta["name"], 
        "current_gwei": current, 
        **fc, 
        **sig
    }

@app.post("/v1/gas/optimize")
async def get_optimize(payload: dict = {"chain_id": 1}):
    """Agent decision engine."""
    chain_id = payload.get("chain_id", 1)
    max_gas = float(payload.get("max_gas_gwei", 50))
    
    meta = CHAIN_MAP.get(chain_id) or CHAIN_MAP[1]
    if meta["source"] == "rpc":
        data = await fetch_gas_rpc(meta["rpc"])
        current = data.get("base_fee_gwei", 25)
    else:
        data = await fetch_eth_gas()
        current = data.get("propose", 35)
        
    fc = forecast(current)
    sig = generate_signal(current, fc["prediction_15m"], fc["prediction_1h"])
    savings = round((current - min(fc["prediction_15m"], fc["prediction_1h"])) * 21000 / 1e9, 4) if sig["signal"] == "WAIT" else 0
    
    return {
        "chain_id": chain_id,
        "current": current,
        "action": sig["signal"],
        "reason": sig["reason"],
        "savings_estimate_eth": savings
    }
