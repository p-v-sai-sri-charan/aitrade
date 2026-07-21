export interface AuditLogEntry {
  id: string;
  timestamp: string;
  originalTranscript?: string;
  detectedLanguage?: string;
  // The backend stores the parsed TradeIntent as raw JSON for audit purposes;
  // it is not re-validated on read, so it's typed loosely here.
  parsedIntent?: Record<string, unknown>;
  aiProvider?: string;
  validationValid: boolean;
  validationErrors: string[];
  // Similarly a loosely-typed snapshot of the RiskCheckResult at the time.
  riskCheck?: Record<string, unknown>;
  userConfirmed?: boolean;
  orderResponseSummary?: string;
  orderId?: string;
}
