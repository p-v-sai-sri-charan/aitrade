export type AIProviderName =
  | "mock"
  | "anthropic"
  | "openai"
  | "gemini"
  | "local"
  | "ollama";

export type LanguagePreference = "hi-IN" | "en-IN" | "hinglish" | "auto";

export interface RiskLimits {
  maxOrderValue: number;
  maxQuantity: number;
  maxPriceDeviationPct: number;
  dailyLossLimit: number;
}

export interface UserSettings {
  aiProvider: AIProviderName;
  languagePreference: LanguagePreference;
  voiceOutputEnabled: boolean;
  riskLimits: RiskLimits;
  tradingKillSwitch: boolean;
}
