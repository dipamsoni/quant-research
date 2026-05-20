#!/usr/bin/env python3
"""Generate assets_seed_data.json from NSE Nifty 500 + top 50 crypto.

Primary source: NSE archives CSV (fetched with browser User-Agent).
Fallback: hardcoded list of ~200 major NSE stocks across all sectors.

Run:
    uv run python scripts/generate_seed_data.py

Overwrites scripts/assets_seed_data.json. Re-running is safe.
"""

from __future__ import annotations

import io
import json
from pathlib import Path

_OUT = Path(__file__).parent / "assets_seed_data.json"

# ── Top 50 crypto by market cap (Binance USDT spot pairs) ─────────────────────
_CRYPTO: list[dict] = [
    {"symbol": "BTCUSDT",   "name": "Bitcoin",           "industry": "Layer 1"},
    {"symbol": "ETHUSDT",   "name": "Ethereum",          "industry": "Layer 1"},
    {"symbol": "BNBUSDT",   "name": "BNB",               "industry": "Exchange Token"},
    {"symbol": "SOLUSDT",   "name": "Solana",            "industry": "Layer 1"},
    {"symbol": "XRPUSDT",   "name": "XRP",               "industry": "Payments"},
    {"symbol": "USDCUSDT",  "name": "USD Coin",          "industry": "Stablecoin"},
    {"symbol": "ADAUSDT",   "name": "Cardano",           "industry": "Layer 1"},
    {"symbol": "AVAXUSDT",  "name": "Avalanche",         "industry": "Layer 1"},
    {"symbol": "DOGEUSDT",  "name": "Dogecoin",          "industry": "Meme"},
    {"symbol": "TRXUSDT",   "name": "TRON",              "industry": "Layer 1"},
    {"symbol": "DOTUSDT",   "name": "Polkadot",          "industry": "Layer 0"},
    {"symbol": "MATICUSDT", "name": "Polygon",           "industry": "Layer 2"},
    {"symbol": "LINKUSDT",  "name": "Chainlink",         "industry": "Oracle"},
    {"symbol": "LTCUSDT",   "name": "Litecoin",          "industry": "Payments"},
    {"symbol": "SHIBUSDT",  "name": "Shiba Inu",         "industry": "Meme"},
    {"symbol": "UNIUSDT",   "name": "Uniswap",           "industry": "DeFi"},
    {"symbol": "ATOMUSDT",  "name": "Cosmos",            "industry": "Layer 0"},
    {"symbol": "ETCUSDT",   "name": "Ethereum Classic",  "industry": "Layer 1"},
    {"symbol": "XMRUSDT",   "name": "Monero",            "industry": "Privacy"},
    {"symbol": "XLMUSDT",   "name": "Stellar",           "industry": "Payments"},
    {"symbol": "ALGOUSDT",  "name": "Algorand",          "industry": "Layer 1"},
    {"symbol": "AAVEUSDT",  "name": "Aave",              "industry": "DeFi"},
    {"symbol": "APTUSDT",   "name": "Aptos",             "industry": "Layer 1"},
    {"symbol": "NEARUSDT",  "name": "NEAR Protocol",     "industry": "Layer 1"},
    {"symbol": "GRTUSDT",   "name": "The Graph",         "industry": "Indexing"},
    {"symbol": "OPUSDT",    "name": "Optimism",          "industry": "Layer 2"},
    {"symbol": "ARBUSDT",   "name": "Arbitrum",          "industry": "Layer 2"},
    {"symbol": "MKRUSDT",   "name": "Maker",             "industry": "DeFi"},
    {"symbol": "INJUSDT",   "name": "Injective",         "industry": "Layer 1"},
    {"symbol": "SUIUSDT",   "name": "Sui",               "industry": "Layer 1"},
    {"symbol": "SEIUSDT",   "name": "Sei",               "industry": "Layer 1"},
    {"symbol": "LDOUSDT",   "name": "Lido DAO",          "industry": "DeFi"},
    {"symbol": "STXUSDT",   "name": "Stacks",            "industry": "Bitcoin L2"},
    {"symbol": "PEPEUSDT",  "name": "Pepe",              "industry": "Meme"},
    {"symbol": "WLDUSDT",   "name": "Worldcoin",         "industry": "Identity"},
    {"symbol": "TIAUSDT",   "name": "Celestia",          "industry": "Data Availability"},
    {"symbol": "JUPUSDT",   "name": "Jupiter",           "industry": "DeFi"},
    {"symbol": "ENAUSDT",   "name": "Ethena",            "industry": "Stablecoin"},
    {"symbol": "RENDERUSDT","name": "Render",            "industry": "GPU Computing"},
    {"symbol": "FETUSDT",   "name": "Fetch.ai",          "industry": "AI"},
    {"symbol": "AGIXUSDT",  "name": "SingularityNET",    "industry": "AI"},
    {"symbol": "TAOUSDT",   "name": "Bittensor",         "industry": "AI"},
    {"symbol": "RUNEUSDT",  "name": "THORChain",         "industry": "DeFi"},
    {"symbol": "FLOKIUSDT", "name": "FLOKI",             "industry": "Meme"},
    {"symbol": "EIGENUSDT", "name": "EigenLayer",        "industry": "Restaking"},
    {"symbol": "POLUSDT",   "name": "POL (ex-MATIC)",    "industry": "Layer 2"},
    {"symbol": "QNTUSDT",   "name": "Quant",             "industry": "Interoperability"},
    {"symbol": "VETUSDT",   "name": "VeChain",           "industry": "Supply Chain"},
    {"symbol": "FILUSDT",   "name": "Filecoin",          "industry": "Storage"},
    {"symbol": "OCEANUSDT", "name": "Ocean Protocol",    "industry": "AI"},
]

# ── Hardcoded Nifty 500 fallback (~230 major NSE stocks) ─────────────────────
# Symbol format: yfinance NSE ticker (no .NS suffix — provider appends it)
_NSE_FALLBACK: list[dict] = [
    # Large Cap — IT / Technology
    {"symbol": "TCS",         "name": "Tata Consultancy Services",   "sector": "Information Technology", "industry": "IT Services"},
    {"symbol": "INFY",        "name": "Infosys",                      "sector": "Information Technology", "industry": "IT Services"},
    {"symbol": "WIPRO",       "name": "Wipro",                        "sector": "Information Technology", "industry": "IT Services"},
    {"symbol": "HCLTECH",     "name": "HCL Technologies",             "sector": "Information Technology", "industry": "IT Services"},
    {"symbol": "TECHM",       "name": "Tech Mahindra",                "sector": "Information Technology", "industry": "IT Services"},
    {"symbol": "LTIM",        "name": "LTIMindtree",                  "sector": "Information Technology", "industry": "IT Services"},
    {"symbol": "MPHASIS",     "name": "Mphasis",                      "sector": "Information Technology", "industry": "IT Services"},
    {"symbol": "COFORGE",     "name": "Coforge",                      "sector": "Information Technology", "industry": "IT Services"},
    {"symbol": "PERSISTENT",  "name": "Persistent Systems",           "sector": "Information Technology", "industry": "IT Services"},
    {"symbol": "OFSS",        "name": "Oracle Financial Services",    "sector": "Information Technology", "industry": "IT Services"},
    {"symbol": "KPITTECH",    "name": "KPIT Technologies",            "sector": "Information Technology", "industry": "IT Services"},
    # Large Cap — Banking
    {"symbol": "HDFCBANK",    "name": "HDFC Bank",                    "sector": "Financial Services", "industry": "Private Sector Bank"},
    {"symbol": "ICICIBANK",   "name": "ICICI Bank",                   "sector": "Financial Services", "industry": "Private Sector Bank"},
    {"symbol": "SBIN",        "name": "State Bank of India",          "sector": "Financial Services", "industry": "Public Sector Bank"},
    {"symbol": "KOTAKBANK",   "name": "Kotak Mahindra Bank",          "sector": "Financial Services", "industry": "Private Sector Bank"},
    {"symbol": "AXISBANK",    "name": "Axis Bank",                    "sector": "Financial Services", "industry": "Private Sector Bank"},
    {"symbol": "INDUSINDBK",  "name": "IndusInd Bank",                "sector": "Financial Services", "industry": "Private Sector Bank"},
    {"symbol": "BANKBARODA",  "name": "Bank of Baroda",               "sector": "Financial Services", "industry": "Public Sector Bank"},
    {"symbol": "PNB",         "name": "Punjab National Bank",         "sector": "Financial Services", "industry": "Public Sector Bank"},
    {"symbol": "CANBK",       "name": "Canara Bank",                  "sector": "Financial Services", "industry": "Public Sector Bank"},
    {"symbol": "UNIONBANK",   "name": "Union Bank of India",          "sector": "Financial Services", "industry": "Public Sector Bank"},
    {"symbol": "FEDERALBNK",  "name": "Federal Bank",                 "sector": "Financial Services", "industry": "Private Sector Bank"},
    {"symbol": "IDFCFIRSTB",  "name": "IDFC First Bank",              "sector": "Financial Services", "industry": "Private Sector Bank"},
    {"symbol": "BANDHANBNK",  "name": "Bandhan Bank",                 "sector": "Financial Services", "industry": "Private Sector Bank"},
    {"symbol": "AUBANK",      "name": "AU Small Finance Bank",        "sector": "Financial Services", "industry": "Small Finance Bank"},
    {"symbol": "RBLBANK",     "name": "RBL Bank",                     "sector": "Financial Services", "industry": "Private Sector Bank"},
    # Financial Services / NBFC
    {"symbol": "BAJFINANCE",  "name": "Bajaj Finance",                "sector": "Financial Services", "industry": "NBFC"},
    {"symbol": "BAJAJFINSV",  "name": "Bajaj Finserv",                "sector": "Financial Services", "industry": "NBFC"},
    {"symbol": "CHOLAFIN",    "name": "Cholamandalam Investment",     "sector": "Financial Services", "industry": "NBFC"},
    {"symbol": "MUTHOOTFIN",  "name": "Muthoot Finance",              "sector": "Financial Services", "industry": "NBFC"},
    {"symbol": "MANAPPURAM",  "name": "Manappuram Finance",           "sector": "Financial Services", "industry": "NBFC"},
    {"symbol": "SHRIRAMFIN",  "name": "Shriram Finance",              "sector": "Financial Services", "industry": "NBFC"},
    {"symbol": "LICHSGFIN",   "name": "LIC Housing Finance",          "sector": "Financial Services", "industry": "Housing Finance"},
    {"symbol": "PNBHOUSING",  "name": "PNB Housing Finance",          "sector": "Financial Services", "industry": "Housing Finance"},
    {"symbol": "M&MFIN",      "name": "Mahindra & Mahindra Financial","sector": "Financial Services", "industry": "NBFC"},
    # Insurance
    {"symbol": "HDFCLIFE",    "name": "HDFC Life Insurance",          "sector": "Financial Services", "industry": "Life Insurance"},
    {"symbol": "SBILIFE",     "name": "SBI Life Insurance",           "sector": "Financial Services", "industry": "Life Insurance"},
    {"symbol": "ICICIGI",     "name": "ICICI Lombard General Insur",  "sector": "Financial Services", "industry": "General Insurance"},
    {"symbol": "NIACL",       "name": "New India Assurance",          "sector": "Financial Services", "industry": "General Insurance"},
    {"symbol": "STARHEALTH",  "name": "Star Health Insurance",        "sector": "Financial Services", "industry": "Health Insurance"},
    {"symbol": "LICI",        "name": "Life Insurance Corp of India", "sector": "Financial Services", "industry": "Life Insurance"},
    # Capital Markets
    {"symbol": "BSE",         "name": "BSE Ltd",                      "sector": "Financial Services", "industry": "Capital Markets"},
    {"symbol": "CDSL",        "name": "CDSL",                         "sector": "Financial Services", "industry": "Capital Markets"},
    {"symbol": "MCX",         "name": "Multi Commodity Exchange",     "sector": "Financial Services", "industry": "Capital Markets"},
    {"symbol": "IEX",         "name": "Indian Energy Exchange",       "sector": "Financial Services", "industry": "Capital Markets"},
    # Oil & Gas / Energy
    {"symbol": "RELIANCE",    "name": "Reliance Industries",          "sector": "Oil Gas & Consumable Fuels", "industry": "Refineries"},
    {"symbol": "ONGC",        "name": "Oil & Natural Gas Corp",       "sector": "Oil Gas & Consumable Fuels", "industry": "Exploration"},
    {"symbol": "BPCL",        "name": "Bharat Petroleum Corp",        "sector": "Oil Gas & Consumable Fuels", "industry": "Refineries"},
    {"symbol": "IOC",         "name": "Indian Oil Corporation",       "sector": "Oil Gas & Consumable Fuels", "industry": "Refineries"},
    {"symbol": "HINDPETRO",   "name": "Hindustan Petroleum Corp",     "sector": "Oil Gas & Consumable Fuels", "industry": "Refineries"},
    {"symbol": "GAIL",        "name": "GAIL (India)",                 "sector": "Oil Gas & Consumable Fuels", "industry": "Gas Distribution"},
    {"symbol": "PETRONET",    "name": "Petronet LNG",                 "sector": "Oil Gas & Consumable Fuels", "industry": "Gas Distribution"},
    {"symbol": "IGL",         "name": "Indraprastha Gas",             "sector": "Oil Gas & Consumable Fuels", "industry": "Gas Distribution"},
    {"symbol": "MGL",         "name": "Mahanagar Gas",                "sector": "Oil Gas & Consumable Fuels", "industry": "Gas Distribution"},
    {"symbol": "GUJGASLTD",   "name": "Gujarat Gas",                  "sector": "Oil Gas & Consumable Fuels", "industry": "Gas Distribution"},
    # Telecom
    {"symbol": "BHARTIARTL",  "name": "Bharti Airtel",                "sector": "Telecommunication", "industry": "Telecom Services"},
    {"symbol": "TATACOMM",    "name": "Tata Communications",          "sector": "Telecommunication", "industry": "Telecom Services"},
    {"symbol": "INDUSTOWER",  "name": "Indus Towers",                 "sector": "Telecommunication", "industry": "Telecom Infrastructure"},
    # Automobile
    {"symbol": "MARUTI",      "name": "Maruti Suzuki India",          "sector": "Automobile", "industry": "Passenger Vehicles"},
    {"symbol": "TATAMOTORS",  "name": "Tata Motors",                  "sector": "Automobile", "industry": "Commercial Vehicles"},
    {"symbol": "M&M",         "name": "Mahindra & Mahindra",          "sector": "Automobile", "industry": "Utility Vehicles"},
    {"symbol": "BAJAJ-AUTO",  "name": "Bajaj Auto",                   "sector": "Automobile", "industry": "Two & Three Wheelers"},
    {"symbol": "EICHERMOT",   "name": "Eicher Motors",                "sector": "Automobile", "industry": "Two & Three Wheelers"},
    {"symbol": "HEROMOTOCO",  "name": "Hero MotoCorp",                "sector": "Automobile", "industry": "Two & Three Wheelers"},
    {"symbol": "TVSMOTORS",   "name": "TVS Motor Company",            "sector": "Automobile", "industry": "Two & Three Wheelers"},
    {"symbol": "ASHOKLEY",    "name": "Ashok Leyland",                "sector": "Automobile", "industry": "Commercial Vehicles"},
    {"symbol": "BALKRISIND",  "name": "Balkrishna Industries",        "sector": "Automobile", "industry": "Tyres"},
    {"symbol": "APOLLOTYRE",  "name": "Apollo Tyres",                 "sector": "Automobile", "industry": "Tyres"},
    {"symbol": "CEATLTD",     "name": "CEAT",                         "sector": "Automobile", "industry": "Tyres"},
    {"symbol": "MOTHERSON",   "name": "Samvardhana Motherson",        "sector": "Automobile", "industry": "Auto Ancillaries"},
    {"symbol": "BOSCHLTD",    "name": "Bosch",                        "sector": "Automobile", "industry": "Auto Ancillaries"},
    {"symbol": "MINDA",       "name": "Minda Industries",             "sector": "Automobile", "industry": "Auto Ancillaries"},
    # Consumer / FMCG
    {"symbol": "HINDUNILVR",  "name": "Hindustan Unilever",           "sector": "Fast Moving Consumer Goods", "industry": "FMCG"},
    {"symbol": "ITC",         "name": "ITC",                          "sector": "Fast Moving Consumer Goods", "industry": "Cigarettes & FMCG"},
    {"symbol": "NESTLEIND",   "name": "Nestle India",                 "sector": "Fast Moving Consumer Goods", "industry": "FMCG"},
    {"symbol": "DABUR",       "name": "Dabur India",                  "sector": "Fast Moving Consumer Goods", "industry": "FMCG"},
    {"symbol": "GODREJCP",    "name": "Godrej Consumer Products",     "sector": "Fast Moving Consumer Goods", "industry": "FMCG"},
    {"symbol": "MARICO",      "name": "Marico",                       "sector": "Fast Moving Consumer Goods", "industry": "FMCG"},
    {"symbol": "COLPAL",      "name": "Colgate-Palmolive (India)",    "sector": "Fast Moving Consumer Goods", "industry": "FMCG"},
    {"symbol": "EMAMILTD",    "name": "Emami",                        "sector": "Fast Moving Consumer Goods", "industry": "FMCG"},
    {"symbol": "TATACONSUM",  "name": "Tata Consumer Products",       "sector": "Fast Moving Consumer Goods", "industry": "FMCG"},
    {"symbol": "VBL",         "name": "Varun Beverages",              "sector": "Fast Moving Consumer Goods", "industry": "Beverages"},
    {"symbol": "RADICO",      "name": "Radico Khaitan",               "sector": "Fast Moving Consumer Goods", "industry": "Beverages"},
    {"symbol": "MCDOWELL-N",  "name": "United Spirits",               "sector": "Fast Moving Consumer Goods", "industry": "Beverages"},
    {"symbol": "UBL",         "name": "United Breweries",             "sector": "Fast Moving Consumer Goods", "industry": "Beverages"},
    # Pharma / Healthcare
    {"symbol": "SUNPHARMA",   "name": "Sun Pharmaceutical Industries","sector": "Healthcare", "industry": "Pharmaceuticals"},
    {"symbol": "DIVISLAB",    "name": "Divi's Laboratories",          "sector": "Healthcare", "industry": "Pharmaceuticals"},
    {"symbol": "CIPLA",       "name": "Cipla",                        "sector": "Healthcare", "industry": "Pharmaceuticals"},
    {"symbol": "DRREDDY",     "name": "Dr Reddy's Laboratories",      "sector": "Healthcare", "industry": "Pharmaceuticals"},
    {"symbol": "AUROPHARMA",  "name": "Aurobindo Pharma",             "sector": "Healthcare", "industry": "Pharmaceuticals"},
    {"symbol": "BIOCON",      "name": "Biocon",                       "sector": "Healthcare", "industry": "Pharmaceuticals"},
    {"symbol": "LUPIN",       "name": "Lupin",                        "sector": "Healthcare", "industry": "Pharmaceuticals"},
    {"symbol": "TORNTPHARM",  "name": "Torrent Pharmaceuticals",      "sector": "Healthcare", "industry": "Pharmaceuticals"},
    {"symbol": "ALKEM",       "name": "Alkem Laboratories",           "sector": "Healthcare", "industry": "Pharmaceuticals"},
    {"symbol": "IPCALAB",     "name": "IPCA Laboratories",            "sector": "Healthcare", "industry": "Pharmaceuticals"},
    {"symbol": "ZYDUSLIFE",   "name": "Zydus Lifesciences",           "sector": "Healthcare", "industry": "Pharmaceuticals"},
    {"symbol": "NATCOPHARM",  "name": "Natco Pharma",                 "sector": "Healthcare", "industry": "Pharmaceuticals"},
    {"symbol": "GLAND",       "name": "Gland Pharma",                 "sector": "Healthcare", "industry": "Pharmaceuticals"},
    {"symbol": "APOLLOHOSP",  "name": "Apollo Hospitals Enterprise",  "sector": "Healthcare", "industry": "Hospitals"},
    {"symbol": "FORTIS",      "name": "Fortis Healthcare",            "sector": "Healthcare", "industry": "Hospitals"},
    {"symbol": "MAXHEALTH",   "name": "Max Healthcare Institute",     "sector": "Healthcare", "industry": "Hospitals"},
    {"symbol": "NARAYANAMED", "name": "Narayana Hrudayalaya",         "sector": "Healthcare", "industry": "Hospitals"},
    {"symbol": "THYROCARE",   "name": "Thyrocare Technologies",       "sector": "Healthcare", "industry": "Diagnostics"},
    # Metals & Mining
    {"symbol": "TATASTEEL",   "name": "Tata Steel",                   "sector": "Metals & Mining", "industry": "Steel"},
    {"symbol": "JSWSTEEL",    "name": "JSW Steel",                    "sector": "Metals & Mining", "industry": "Steel"},
    {"symbol": "HINDALCO",    "name": "Hindalco Industries",          "sector": "Metals & Mining", "industry": "Aluminium"},
    {"symbol": "SAIL",        "name": "Steel Authority of India",     "sector": "Metals & Mining", "industry": "Steel"},
    {"symbol": "NMDC",        "name": "NMDC",                         "sector": "Metals & Mining", "industry": "Iron Ore Mining"},
    {"symbol": "HINDZINC",    "name": "Hindustan Zinc",               "sector": "Metals & Mining", "industry": "Zinc"},
    {"symbol": "VEDL",        "name": "Vedanta",                      "sector": "Metals & Mining", "industry": "Diversified Metals"},
    {"symbol": "NATIONALUM",  "name": "National Aluminium Company",   "sector": "Metals & Mining", "industry": "Aluminium"},
    {"symbol": "JINDALSTEL",  "name": "Jindal Steel & Power",         "sector": "Metals & Mining", "industry": "Steel"},
    {"symbol": "COALINDIA",   "name": "Coal India",                   "sector": "Metals & Mining", "industry": "Coal"},
    {"symbol": "MOIL",        "name": "MOIL",                         "sector": "Metals & Mining", "industry": "Manganese"},
    # Cement / Infrastructure / Construction
    {"symbol": "LT",          "name": "Larsen & Toubro",              "sector": "Capital Goods", "industry": "Engineering Projects"},
    {"symbol": "ULTRACEMCO",  "name": "UltraTech Cement",             "sector": "Construction Materials", "industry": "Cement"},
    {"symbol": "GRASIM",      "name": "Grasim Industries",            "sector": "Construction Materials", "industry": "Cement"},
    {"symbol": "AMBUJACEM",   "name": "Ambuja Cements",               "sector": "Construction Materials", "industry": "Cement"},
    {"symbol": "ACC",         "name": "ACC",                          "sector": "Construction Materials", "industry": "Cement"},
    {"symbol": "DALMIACEMB",  "name": "Dalmia Bharat",                "sector": "Construction Materials", "industry": "Cement"},
    {"symbol": "JKCEMENT",    "name": "JK Cement",                    "sector": "Construction Materials", "industry": "Cement"},
    {"symbol": "SHREECEM",    "name": "Shree Cement",                 "sector": "Construction Materials", "industry": "Cement"},
    {"symbol": "NUVOCO",      "name": "Nuvoco Vistas Corp",           "sector": "Construction Materials", "industry": "Cement"},
    # Power / Utilities
    {"symbol": "NTPC",        "name": "NTPC",                         "sector": "Power", "industry": "Power Generation"},
    {"symbol": "POWERGRID",   "name": "Power Grid Corporation",       "sector": "Power", "industry": "Power Transmission"},
    {"symbol": "TATAPOWER",   "name": "Tata Power",                   "sector": "Power", "industry": "Power Generation"},
    {"symbol": "ADANIPOWER",  "name": "Adani Power",                  "sector": "Power", "industry": "Power Generation"},
    {"symbol": "ADANIGREEN",  "name": "Adani Green Energy",           "sector": "Power", "industry": "Renewable Energy"},
    {"symbol": "TORNTPOWER",  "name": "Torrent Power",                "sector": "Power", "industry": "Power Generation"},
    {"symbol": "CESC",        "name": "CESC",                         "sector": "Power", "industry": "Power Generation"},
    {"symbol": "NHPC",        "name": "NHPC",                         "sector": "Power", "industry": "Hydro Power"},
    {"symbol": "SJVN",        "name": "SJVN",                         "sector": "Power", "industry": "Hydro Power"},
    # Adani Group
    {"symbol": "ADANIENT",    "name": "Adani Enterprises",            "sector": "Metals & Mining", "industry": "Diversified"},
    {"symbol": "ADANIPORTS",  "name": "Adani Ports & SEZ",            "sector": "Services", "industry": "Ports"},
    # Real Estate
    {"symbol": "DLF",         "name": "DLF",                          "sector": "Realty", "industry": "Real Estate"},
    {"symbol": "GODREJPROP",  "name": "Godrej Properties",            "sector": "Realty", "industry": "Real Estate"},
    {"symbol": "OBEROIRLTY",  "name": "Oberoi Realty",                "sector": "Realty", "industry": "Real Estate"},
    {"symbol": "PRESTIGE",    "name": "Prestige Estates Projects",    "sector": "Realty", "industry": "Real Estate"},
    {"symbol": "BRIGADE",     "name": "Brigade Enterprises",          "sector": "Realty", "industry": "Real Estate"},
    {"symbol": "SOBHA",       "name": "Sobha",                        "sector": "Realty", "industry": "Real Estate"},
    {"symbol": "PHOENIXLTD",  "name": "The Phoenix Mills",            "sector": "Realty", "industry": "Real Estate"},
    # Consumer Discretionary / Retail
    {"symbol": "TITAN",       "name": "Titan Company",                "sector": "Consumer Durables", "industry": "Watches & Jewellery"},
    {"symbol": "ASIANPAINT",  "name": "Asian Paints",                 "sector": "Consumer Durables", "industry": "Paints"},
    {"symbol": "BRITANNIA",   "name": "Britannia Industries",         "sector": "Fast Moving Consumer Goods", "industry": "Food Products"},
    {"symbol": "PIDILITIND",  "name": "Pidilite Industries",          "sector": "Chemicals", "industry": "Adhesives"},
    {"symbol": "BERGEPAINT",  "name": "Berger Paints India",          "sector": "Consumer Durables", "industry": "Paints"},
    {"symbol": "HAVELLS",     "name": "Havells India",                "sector": "Consumer Durables", "industry": "Electrical Equipment"},
    {"symbol": "VOLTAS",      "name": "Voltas",                       "sector": "Consumer Durables", "industry": "Air Conditioning"},
    {"symbol": "BLUESTARCO",  "name": "Blue Star",                    "sector": "Consumer Durables", "industry": "Air Conditioning"},
    {"symbol": "WHIRLPOOL",   "name": "Whirlpool of India",           "sector": "Consumer Durables", "industry": "Consumer Electronics"},
    {"symbol": "CROMPTON",    "name": "Crompton Greaves Consumer",    "sector": "Consumer Durables", "industry": "Electrical Equipment"},
    {"symbol": "PAGEIND",     "name": "Page Industries",              "sector": "Textile", "industry": "Garments"},
    {"symbol": "ABFRL",       "name": "Aditya Birla Fashion",         "sector": "Textile", "industry": "Garments"},
    {"symbol": "RAYMOND",     "name": "Raymond",                      "sector": "Textile", "industry": "Textile"},
    {"symbol": "VEDANT",      "name": "Vedant Fashions",              "sector": "Textile", "industry": "Garments"},
    # Capital Goods / Engineering
    {"symbol": "BHEL",        "name": "Bharat Heavy Electricals",     "sector": "Capital Goods", "industry": "Heavy Electricals"},
    {"symbol": "SIEMENS",     "name": "Siemens",                      "sector": "Capital Goods", "industry": "Industrial Equipment"},
    {"symbol": "ABB",         "name": "ABB India",                    "sector": "Capital Goods", "industry": "Industrial Equipment"},
    {"symbol": "CUMMINSIND",  "name": "Cummins India",                "sector": "Capital Goods", "industry": "Engines"},
    {"symbol": "THERMAX",     "name": "Thermax",                      "sector": "Capital Goods", "industry": "Industrial Boilers"},
    {"symbol": "AIAENG",      "name": "AIA Engineering",              "sector": "Capital Goods", "industry": "Castings"},
    {"symbol": "TIINDIA",     "name": "Tube Investments of India",    "sector": "Capital Goods", "industry": "Engineering"},
    {"symbol": "GRINDWELL",   "name": "Grindwell Norton",             "sector": "Capital Goods", "industry": "Abrasives"},
    {"symbol": "BEL",         "name": "Bharat Electronics",           "sector": "Capital Goods", "industry": "Defence Electronics"},
    {"symbol": "HAL",         "name": "Hindustan Aeronautics",        "sector": "Capital Goods", "industry": "Defence"},
    {"symbol": "BDL",         "name": "Bharat Dynamics",              "sector": "Capital Goods", "industry": "Defence"},
    {"symbol": "MFSL",        "name": "Max Financial Services",       "sector": "Financial Services", "industry": "Insurance Holding"},
    # Chemicals / Specialty
    {"symbol": "SRF",         "name": "SRF",                          "sector": "Chemicals", "industry": "Specialty Chemicals"},
    {"symbol": "DEEPAKNTR",   "name": "Deepak Nitrite",               "sector": "Chemicals", "industry": "Specialty Chemicals"},
    {"symbol": "NAVINFLUOR",  "name": "Navin Fluorine International", "sector": "Chemicals", "industry": "Specialty Chemicals"},
    {"symbol": "ATUL",        "name": "Atul",                         "sector": "Chemicals", "industry": "Specialty Chemicals"},
    {"symbol": "CLEAN",       "name": "Clean Science and Technology", "sector": "Chemicals", "industry": "Specialty Chemicals"},
    {"symbol": "PIIND",       "name": "PI Industries",                "sector": "Chemicals", "industry": "Agrochemicals"},
    {"symbol": "RALLIS",      "name": "Rallis India",                 "sector": "Chemicals", "industry": "Agrochemicals"},
    # Logistics / Infrastructure
    {"symbol": "CONCOR",      "name": "Container Corp of India",      "sector": "Services", "industry": "Logistics"},
    {"symbol": "BLUEDART",    "name": "Blue Dart Express",            "sector": "Services", "industry": "Courier"},
    {"symbol": "DELHIVERY",   "name": "Delhivery",                    "sector": "Services", "industry": "Logistics"},
    {"symbol": "IRCTC",       "name": "Indian Railway Catering & Tourism","sector": "Services", "industry": "Tourism"},
    # Hotels / Hospitality
    {"symbol": "INDHOTEL",    "name": "Indian Hotels Company",        "sector": "Services", "industry": "Hotels"},
    {"symbol": "LEMONTREE",   "name": "Lemon Tree Hotels",            "sector": "Services", "industry": "Hotels"},
    {"symbol": "EIHOTEL",     "name": "EIH",                          "sector": "Services", "industry": "Hotels"},
    # Media / Entertainment
    {"symbol": "ZEEL",        "name": "Zee Entertainment Enterprises","sector": "Media Entertainment & Publication", "industry": "Television"},
    {"symbol": "SUNTV",       "name": "Sun TV Network",               "sector": "Media Entertainment & Publication", "industry": "Television"},
    {"symbol": "PVRINOX",     "name": "PVR INOX",                     "sector": "Media Entertainment & Publication", "industry": "Multiplex"},
    # Aviation
    {"symbol": "INDIGO",      "name": "InterGlobe Aviation (IndiGo)", "sector": "Services", "industry": "Airlines"},
    # Education
    {"symbol": "NAUKRI",      "name": "Info Edge (India)",            "sector": "Services", "industry": "Online Classifieds"},
    # New-Age Tech / E-Commerce
    {"symbol": "ZOMATO",      "name": "Zomato",                       "sector": "Consumer Services", "industry": "Food Delivery"},
    {"symbol": "NYKAA",       "name": "FSN E-Commerce Ventures (Nykaa)","sector": "Consumer Services", "industry": "E-Commerce"},
    {"symbol": "PAYTM",       "name": "One 97 Communications (Paytm)","sector": "Financial Services", "industry": "Fintech"},
    {"symbol": "POLICYBZR",   "name": "PB Fintech (Policybazaar)",    "sector": "Financial Services", "industry": "Insurance Tech"},
    # Government / PSU
    {"symbol": "PFC",         "name": "Power Finance Corporation",    "sector": "Financial Services", "industry": "Financial Institution"},
    {"symbol": "RECLTD",      "name": "REC",                          "sector": "Financial Services", "industry": "Financial Institution"},
    {"symbol": "IRFC",        "name": "Indian Railway Finance Corp",  "sector": "Financial Services", "industry": "Financial Institution"},
    {"symbol": "HUDCO",       "name": "Housing and Urban Dev Corp",   "sector": "Financial Services", "industry": "Financial Institution"},
    {"symbol": "SJVN",        "name": "SJVN",                         "sector": "Power", "industry": "Hydro Power"},
    # Sugar
    {"symbol": "BALRAMCHIN",  "name": "Balrampur Chini Mills",        "sector": "Fast Moving Consumer Goods", "industry": "Sugar"},
    {"symbol": "RENUKA",      "name": "Shree Renuka Sugars",          "sector": "Fast Moving Consumer Goods", "industry": "Sugar"},
    # Food / Agri
    {"symbol": "KRBL",        "name": "KRBL",                         "sector": "Fast Moving Consumer Goods", "industry": "Rice"},
    {"symbol": "JUBLFOOD",    "name": "Jubilant Foodworks",           "sector": "Consumer Services", "industry": "Quick Service Restaurant"},
    {"symbol": "DEVYANI",     "name": "Devyani International",        "sector": "Consumer Services", "industry": "Quick Service Restaurant"},
    # Miscellaneous
    {"symbol": "3MINDIA",     "name": "3M India",                     "sector": "Consumer Durables", "industry": "Diversified"},
    {"symbol": "TRENT",       "name": "Trent",                        "sector": "Consumer Services", "industry": "Retail"},
    {"symbol": "DMART",       "name": "Avenue Supermarts (DMart)",    "sector": "Consumer Services", "industry": "Retail"},
    {"symbol": "TTKPRESTIG",  "name": "TTK Prestige",                 "sector": "Consumer Durables", "industry": "Kitchen Appliances"},
]


def _build_crypto() -> list[dict]:
    return [
        {
            "symbol": c["symbol"],
            "name": c["name"],
            "asset_type": "crypto",
            "exchange": "BINANCE",
            "currency": "USDT",
            "sector": "Crypto",
            "industry": c.get("industry", ""),
        }
        for c in _CRYPTO
    ]


def _build_nse_asset(row: dict) -> dict:
    """Convert a raw NSE row (from CSV or fallback list) to seed asset dict."""
    symbol = str(row.get("symbol", row.get("Symbol", ""))).strip()
    name = str(row.get("name", row.get("Company Name", ""))).strip()
    sector = str(row.get("sector", row.get("Industry", ""))).strip()
    industry = str(row.get("industry", "")).strip()
    return {
        "symbol": symbol,
        "name": name,
        "asset_type": "stock",
        "exchange": "NSE",
        "currency": "INR",
        "sector": sector,
        "industry": industry,
    }


def _fetch_nse_nifty500() -> list[dict]:
    """Fetch Nifty 500 constituents from NSE archives CSV."""
    try:
        import pandas as pd
        import requests
    except ImportError:
        raise SystemExit("pandas + requests required")

    url = "https://archives.nseindia.com/content/indices/ind_nifty500list.csv"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/125.0 Safari/537.36"
        ),
        "Referer": "https://www.nseindia.com/",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }
    resp = requests.get(url, headers=headers, timeout=30)
    resp.raise_for_status()

    import io
    df = pd.read_csv(io.StringIO(resp.text))
    # NSE CSV columns: Company Name, Industry, Symbol, Series, ISIN Code
    assets = []
    for _, row in df.iterrows():
        symbol = str(row.get("Symbol", "")).strip()
        name = str(row.get("Company Name", "")).strip()
        sector = str(row.get("Industry", "")).strip()
        if symbol and name:
            assets.append({
                "symbol": symbol,
                "name": name,
                "asset_type": "stock",
                "exchange": "NSE",
                "currency": "INR",
                "sector": sector,
                "industry": sector,
            })
    return assets


def main() -> None:
    stocks: list[dict] = []

    print("Fetching Nifty 500 from NSE archives...")
    try:
        stocks = _fetch_nse_nifty500()
        print(f"  {len(stocks)} NSE stocks fetched from live CSV")
    except Exception as exc:
        print(f"  NSE fetch failed ({exc}), using hardcoded fallback ({len(_NSE_FALLBACK)} stocks)")
        stocks = [_build_nse_asset(r) for r in _NSE_FALLBACK]

    crypto = _build_crypto()
    print(f"  {len(crypto)} crypto assets built")

    # Deduplicate by symbol (live fetch may include duplicates)
    seen: set[str] = set()
    deduped: list[dict] = []
    for a in stocks + crypto:
        if a["symbol"] not in seen:
            seen.add(a["symbol"])
            deduped.append(a)

    _OUT.write_text(
        json.dumps({"assets": deduped}, indent=2, ensure_ascii=True),
        encoding="utf-8",
    )
    print(f"Written {len(deduped)} assets to {_OUT}")


if __name__ == "__main__":
    main()
