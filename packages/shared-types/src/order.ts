import type {
  OrderProduct,
  OrderSide,
  OrderType,
  OrderValidity,
  SupportedExchange,
} from "./tradeIntent";

export type OrderStatus =
  | "PENDING"
  | "FILLED"
  | "PARTIALLY_FILLED"
  | "REJECTED"
  | "CANCELLED";

export interface OrderRequest {
  exchange: SupportedExchange;
  symbol: string;
  side: OrderSide;
  quantity: number;
  orderType: OrderType;
  limitPrice?: number;
  product: OrderProduct;
  validity: OrderValidity;
}

export interface OrderPreview {
  previewId: string;
  request: OrderRequest;
  companyName: string;
  estimatedPrice: number;
  estimatedValue: number;
  estimatedBrokerage: number;
  estimatedTaxes: number;
  estimatedTotal: number;
  riskCheck: RiskCheckResult;
  expiresAt: string;
}

export interface Order {
  id: string;
  exchange: SupportedExchange;
  symbol: string;
  companyName: string;
  side: OrderSide;
  quantity: number;
  filledQuantity: number;
  orderType: OrderType;
  limitPrice?: number;
  averageFillPrice?: number;
  product: OrderProduct;
  validity: OrderValidity;
  status: OrderStatus;
  brokerage: number;
  taxes: number;
  rejectionReason?: string;
  createdAt: string;
  updatedAt: string;
}

export interface RiskCheckResult {
  allowed: boolean;
  code: RiskCode | "OK";
  message: string;
  requiresOverride: boolean;
}

export type RiskCode =
  | "ORDER_VALUE_LIMIT_EXCEEDED"
  | "MAX_QUANTITY_EXCEEDED"
  | "INSUFFICIENT_BALANCE"
  | "DUPLICATE_ORDER"
  | "INVALID_PRICE"
  | "PRICE_DEVIATION_TOO_HIGH"
  | "MISSING_FIELDS"
  | "AMBIGUOUS_SYMBOL"
  | "UNSUPPORTED_EXCHANGE"
  | "UNSUPPORTED_PRODUCT"
  | "DAILY_LOSS_LIMIT_EXCEEDED"
  | "TRADING_KILL_SWITCH_ACTIVE"
  | "SYMBOL_NOT_FOUND"
  | "MARKET_CLOSED";
