/**
 * Structured trade intent produced by an AI provider from a voice/text
 * command, and independently re-validated by the backend before any
 * instrument resolution or risk check happens. Never trust this shape
 * without server-side schema validation.
 */

export type SupportedExchange = "NSE";

export type OrderSide = "BUY" | "SELL";

export type OrderType = "MARKET" | "LIMIT";

export type OrderProduct = "DELIVERY";

export type OrderValidity = "DAY";

export type CommandLanguage = "hi-IN" | "en-IN" | "hinglish";

export type TradeIntentType =
  | "PLACE_ORDER"
  | "CANCEL_ORDER"
  | "VIEW_PORTFOLIO"
  | "VIEW_ORDERS"
  | "VIEW_POSITION"
  | "UNKNOWN";

export interface TradeIntent {
  intent: TradeIntentType;
  exchange?: SupportedExchange;
  symbol?: string;
  side?: OrderSide;
  quantity?: number;
  orderType?: OrderType;
  limitPrice?: number;
  product?: OrderProduct;
  validity?: OrderValidity;
  language: CommandLanguage;
  confidence: number;
  missingFields: string[];
  requiresConfirmation: boolean;
  /**
   * Present when the symbol/company name is ambiguous (e.g. "Tata").
   * Each entry is a human-readable "SYMBOL - Company Name" string --
   * the backend never guesses a single exact symbol in this case.
   */
  ambiguousSymbolCandidates?: string[];
  /** Order id the intent refers to, for CANCEL_ORDER intents. */
  orderId?: string;
}

export interface TradeIntentInput {
  transcript: string;
  /** Hint from the client's speech recognizer, if available. */
  detectedLanguage?: CommandLanguage;
  /** Pending context, e.g. an outstanding order awaiting confirmation. */
  conversationContext?: Record<string, unknown>;
}

export interface TradeIntentResult {
  intent: TradeIntent;
  /** Raw provider text, kept for audit/debugging, never executed directly. */
  rawProviderOutput?: string;
  provider: string;
}
