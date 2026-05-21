const SECTOR_MAP: Record<string, string> = {
  // Banking
  HDFCBANK: "Banking", ICICIBANK: "Banking", KOTAKBANK: "Banking",
  SBIN: "Banking", AXISBANK: "Banking", INDUSINDBK: "Banking",
  BANDHANBNK: "Banking", FEDERALBNK: "Banking", IDFCFIRSTB: "Banking",
  PNB: "Banking", BANKBARODA: "Banking", CANBK: "Banking",

  // IT
  TCS: "IT", INFY: "IT", WIPRO: "IT", HCLTECH: "IT",
  TECHM: "IT", LTI: "IT", LTIM: "IT", MPHASIS: "IT",
  COFORGE: "IT", PERSISTENT: "IT", OFSS: "IT",

  // Energy & Oil
  RELIANCE: "Energy", ONGC: "Energy", BPCL: "Energy",
  IOC: "Energy", HINDPETRO: "Energy", GAIL: "Energy",
  NTPC: "Energy", POWERGRID: "Energy", ADANIGREEN: "Energy",
  TATAPOWER: "Energy", ADANIPOWER: "Energy", CESC: "Energy",

  // Pharma
  SUNPHARMA: "Pharma", DRREDDY: "Pharma", CIPLA: "Pharma",
  DIVISLAB: "Pharma", LUPIN: "Pharma", AUROPHARMA: "Pharma",
  TORNTPHARM: "Pharma", ALKEM: "Pharma", BIOCON: "Pharma",

  // Auto
  MARUTI: "Auto", TATAMOTORS: "Auto", "M&M": "Auto",
  BAJAJ_AUTO: "Auto", EICHERMOT: "Auto", HEROMOTOCO: "Auto",
  TVSMOTOR: "Auto", ASHOKLEY: "Auto", BALKRISIND: "Auto",

  // FMCG
  HINDUNILVR: "FMCG", ITC: "FMCG", NESTLEIND: "FMCG",
  BRITANNIA: "FMCG", DABUR: "FMCG", GODREJCP: "FMCG",
  MARICO: "FMCG", EMAMILTD: "FMCG", COLPAL: "FMCG",

  // Finance / NBFC
  BAJFINANCE: "Finance", BAJAJFINSV: "Finance", CHOLAFIN: "Finance",
  MUTHOOTFIN: "Finance", HDFCLIFE: "Finance", SBILIFE: "Finance",
  ICICIGI: "Finance", SBICARD: "Finance", MANAPPURAM: "Finance",

  // Metals
  TATASTEEL: "Metals", JSWSTEEL: "Metals", HINDALCO: "Metals",
  VEDL: "Metals", COALINDIA: "Metals", NMDC: "Metals",
  SAIL: "Metals", NATIONALUM: "Metals",

  // Infrastructure / Cement
  LT: "Infra", ULTRACEMCO: "Infra", GRASIM: "Infra",
  ACC: "Infra", AMBUJACEM: "Infra", ADANIPORTS: "Infra",
  SIEMENS: "Infra", ABB: "Infra", BHEL: "Infra",

  // Telecom
  BHARTIARTL: "Telecom", IDEA: "Telecom",
};

export function sectorOf(symbol: string): string {
  return SECTOR_MAP[symbol.toUpperCase()] ?? "Others";
}
