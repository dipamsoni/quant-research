#!/usr/bin/env python3
"""Generate assets_seed_data.json from S&P 500 (Wikipedia) + top 50 crypto.

Requires: pandas, lxml (already in dev deps via yfinance)

Run:
    uv run python scripts/generate_seed_data.py

Overwrites scripts/assets_seed_data.json. Re-running is safe.
"""

from __future__ import annotations

import json
from pathlib import Path

_OUT = Path(__file__).parent / "assets_seed_data.json"

# Top 50 crypto by market cap (symbols used on Binance spot)
_CRYPTO: list[dict] = [
    {"symbol": "BTCUSDT",  "name": "Bitcoin",           "exchange": "BINANCE", "sector": "Crypto", "industry": "Layer 1"},
    {"symbol": "ETHUSDT",  "name": "Ethereum",          "exchange": "BINANCE", "sector": "Crypto", "industry": "Layer 1"},
    {"symbol": "BNBUSDT",  "name": "BNB",               "exchange": "BINANCE", "sector": "Crypto", "industry": "Exchange Token"},
    {"symbol": "SOLUSDT",  "name": "Solana",            "exchange": "BINANCE", "sector": "Crypto", "industry": "Layer 1"},
    {"symbol": "XRPUSDT",  "name": "XRP",               "exchange": "BINANCE", "sector": "Crypto", "industry": "Payments"},
    {"symbol": "USDCUSDT", "name": "USD Coin",          "exchange": "BINANCE", "sector": "Crypto", "industry": "Stablecoin"},
    {"symbol": "ADAUSDT",  "name": "Cardano",           "exchange": "BINANCE", "sector": "Crypto", "industry": "Layer 1"},
    {"symbol": "AVAXUSDT", "name": "Avalanche",         "exchange": "BINANCE", "sector": "Crypto", "industry": "Layer 1"},
    {"symbol": "DOGEUSDT", "name": "Dogecoin",          "exchange": "BINANCE", "sector": "Crypto", "industry": "Meme"},
    {"symbol": "TRXUSDT",  "name": "TRON",              "exchange": "BINANCE", "sector": "Crypto", "industry": "Layer 1"},
    {"symbol": "DOTUSDT",  "name": "Polkadot",          "exchange": "BINANCE", "sector": "Crypto", "industry": "Layer 0"},
    {"symbol": "MATICUSDT","name": "Polygon",           "exchange": "BINANCE", "sector": "Crypto", "industry": "Layer 2"},
    {"symbol": "LINKUSDT", "name": "Chainlink",         "exchange": "BINANCE", "sector": "Crypto", "industry": "Oracle"},
    {"symbol": "LTCUSDT",  "name": "Litecoin",          "exchange": "BINANCE", "sector": "Crypto", "industry": "Payments"},
    {"symbol": "SHIBUSDT", "name": "Shiba Inu",         "exchange": "BINANCE", "sector": "Crypto", "industry": "Meme"},
    {"symbol": "UNIUSDT",  "name": "Uniswap",           "exchange": "BINANCE", "sector": "Crypto", "industry": "DeFi"},
    {"symbol": "ATOMUSDT", "name": "Cosmos",            "exchange": "BINANCE", "sector": "Crypto", "industry": "Layer 0"},
    {"symbol": "ETCUSDT",  "name": "Ethereum Classic",  "exchange": "BINANCE", "sector": "Crypto", "industry": "Layer 1"},
    {"symbol": "XMRUSDT",  "name": "Monero",            "exchange": "BINANCE", "sector": "Crypto", "industry": "Privacy"},
    {"symbol": "XLMUSDT",  "name": "Stellar",           "exchange": "BINANCE", "sector": "Crypto", "industry": "Payments"},
    {"symbol": "ALGOUSDT", "name": "Algorand",          "exchange": "BINANCE", "sector": "Crypto", "industry": "Layer 1"},
    {"symbol": "VETUSDT",  "name": "VeChain",           "exchange": "BINANCE", "sector": "Crypto", "industry": "Supply Chain"},
    {"symbol": "FILUSDT",  "name": "Filecoin",          "exchange": "BINANCE", "sector": "Crypto", "industry": "Storage"},
    {"symbol": "AAVEUSDT", "name": "Aave",              "exchange": "BINANCE", "sector": "Crypto", "industry": "DeFi"},
    {"symbol": "APTUSDT",  "name": "Aptos",             "exchange": "BINANCE", "sector": "Crypto", "industry": "Layer 1"},
    {"symbol": "NEARUSDT", "name": "NEAR Protocol",     "exchange": "BINANCE", "sector": "Crypto", "industry": "Layer 1"},
    {"symbol": "QNTUSDT",  "name": "Quant",             "exchange": "BINANCE", "sector": "Crypto", "industry": "Interoperability"},
    {"symbol": "GRTUSDT",  "name": "The Graph",         "exchange": "BINANCE", "sector": "Crypto", "industry": "Indexing"},
    {"symbol": "OPUSDT",   "name": "Optimism",          "exchange": "BINANCE", "sector": "Crypto", "industry": "Layer 2"},
    {"symbol": "ARBUSDT",  "name": "Arbitrum",          "exchange": "BINANCE", "sector": "Crypto", "industry": "Layer 2"},
    {"symbol": "MKRUSDT",  "name": "Maker",             "exchange": "BINANCE", "sector": "Crypto", "industry": "DeFi"},
    {"symbol": "INJUSDT",  "name": "Injective",         "exchange": "BINANCE", "sector": "Crypto", "industry": "Layer 1"},
    {"symbol": "SUIUSDT",  "name": "Sui",               "exchange": "BINANCE", "sector": "Crypto", "industry": "Layer 1"},
    {"symbol": "SEIUSDT",  "name": "Sei",               "exchange": "BINANCE", "sector": "Crypto", "industry": "Layer 1"},
    {"symbol": "RUNEUSDT", "name": "THORChain",         "exchange": "BINANCE", "sector": "Crypto", "industry": "DeFi"},
    {"symbol": "LDOUSDT",  "name": "Lido DAO",          "exchange": "BINANCE", "sector": "Crypto", "industry": "DeFi"},
    {"symbol": "STXUSDT",  "name": "Stacks",            "exchange": "BINANCE", "sector": "Crypto", "industry": "Bitcoin L2"},
    {"symbol": "FLOKIUSDT","name": "FLOKI",             "exchange": "BINANCE", "sector": "Crypto", "industry": "Meme"},
    {"symbol": "PEPEUSDT", "name": "Pepe",              "exchange": "BINANCE", "sector": "Crypto", "industry": "Meme"},
    {"symbol": "WLDUSDT",  "name": "Worldcoin",         "exchange": "BINANCE", "sector": "Crypto", "industry": "Identity"},
    {"symbol": "TIAUSDT",  "name": "Celestia",          "exchange": "BINANCE", "sector": "Crypto", "industry": "Data Availability"},
    {"symbol": "JUPUSDT",  "name": "Jupiter",           "exchange": "BINANCE", "sector": "Crypto", "industry": "DeFi"},
    {"symbol": "EIGENUSDT","name": "EigenLayer",        "exchange": "BINANCE", "sector": "Crypto", "industry": "Restaking"},
    {"symbol": "ENAUSDT",  "name": "Ethena",            "exchange": "BINANCE", "sector": "Crypto", "industry": "Stablecoin"},
    {"symbol": "POLUSDT",  "name": "POL (ex-MATIC)",   "exchange": "BINANCE", "sector": "Crypto", "industry": "Layer 2"},
    {"symbol": "RENDERUSDT","name": "Render",           "exchange": "BINANCE", "sector": "Crypto", "industry": "GPU Computing"},
    {"symbol": "FETUSDT",  "name": "Fetch.ai",          "exchange": "BINANCE", "sector": "Crypto", "industry": "AI"},
    {"symbol": "AGIXUSDT", "name": "SingularityNET",   "exchange": "BINANCE", "sector": "Crypto", "industry": "AI"},
    {"symbol": "OCEANUSDT","name": "Ocean Protocol",   "exchange": "BINANCE", "sector": "Crypto", "industry": "AI"},
    {"symbol": "TAOUSDT",  "name": "Bittensor",         "exchange": "BINANCE", "sector": "Crypto", "industry": "AI"},
]


def _build_crypto() -> list[dict]:
    return [
        {
            "symbol": c["symbol"],
            "name": c["name"],
            "asset_type": "crypto",
            "exchange": c["exchange"],
            "currency": "USDT",
            "sector": c.get("sector", "Crypto"),
            "industry": c.get("industry", ""),
        }
        for c in _CRYPTO
    ]


def _fetch_sp500() -> list[dict]:
    """Fetch S&P 500 from Wikipedia. Returns list of asset dicts."""
    try:
        import io
        import pandas as pd
        import requests
    except ImportError:
        raise SystemExit("pandas + requests required: uv add pandas lxml requests")

    url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/125.0 Safari/537.36"
        )
    }
    resp = requests.get(url, headers=headers, timeout=30)
    resp.raise_for_status()

    tables = pd.read_html(io.StringIO(resp.text), flavor="lxml")
    sp500 = tables[0]

    assets = []
    for _, row in sp500.iterrows():
        symbol = str(row["Symbol"]).replace(".", "-").strip()
        name = str(row["Security"]).strip()
        exchange = str(row.get("Exchange", "NYSE")).strip()
        sector = str(row.get("GICS Sector", "")).strip()
        industry = str(row.get("GICS Sub-Industry", "")).strip()
        assets.append(
            {
                "symbol": symbol,
                "name": name,
                "asset_type": "stock",
                "exchange": exchange,
                "currency": "USD",
                "sector": sector,
                "industry": industry,
            }
        )
    return assets


def main() -> None:
    print("Fetching S&P 500 from Wikipedia…")
    stocks = _fetch_sp500()
    print(f"  {len(stocks)} S&P 500 stocks fetched")

    crypto = _build_crypto()
    print(f"  {len(crypto)} crypto assets built")

    assets = stocks + crypto
    _OUT.write_text(json.dumps({"assets": assets}, indent=2, ensure_ascii=False))
    print(f"Written {len(assets)} assets to {_OUT}")


if __name__ == "__main__":
    main()
