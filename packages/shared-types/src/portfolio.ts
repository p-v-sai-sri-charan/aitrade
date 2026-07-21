export interface Position {
  symbol: string;
  companyName: string;
  quantity: number;
  averagePrice: number;
  currentPrice: number;
  unrealizedPnl: number;
  unrealizedPnlPct: number;
  realizedPnl: number;
}

export interface Portfolio {
  availableBalance: number;
  usedMargin: number;
  portfolioValue: number;
  totalInvested: number;
  dayPnl: number;
  dayPnlPct: number;
  totalPnl: number;
  positions: Position[];
}

export interface Quote {
  symbol: string;
  companyName: string;
  lastPrice: number;
  previousClose: number;
  changePct: number;
  updatedAt: string;
}

export interface Instrument {
  symbol: string;
  companyName: string;
  exchange: "NSE";
}

export interface InstrumentStatus {
  source: string;
  instrumentCount: number;
  lastRefreshedAt: string | null;
}
