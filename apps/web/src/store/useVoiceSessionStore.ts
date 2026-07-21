import { create } from "zustand";
import type { Order, OrderPreview, TradeIntent } from "@vaanitrade/shared-types";

export type VoiceSessionStatus =
  | "idle"
  | "listening"
  | "processing"
  | "awaiting_confirmation"
  | "confirming"
  | "placed"
  | "error";

interface VoiceSessionState {
  status: VoiceSessionStatus;
  interimTranscript: string;
  finalTranscript: string;
  parsedIntent: TradeIntent | null;
  aiProvider: string | null;
  orderPreview: OrderPreview | null;
  lastOrder: Order | null;
  errorMessage: string | null;
  idempotencyKey: string | null;

  setListening: () => void;
  setInterimTranscript: (text: string) => void;
  setFinalTranscript: (text: string) => void;
  setProcessing: () => void;
  setParsedIntent: (intent: TradeIntent, provider: string) => void;
  setOrderPreview: (preview: OrderPreview) => void;
  setConfirming: () => void;
  setPlaced: (order: Order) => void;
  setError: (message: string) => void;
  reset: () => void;
}

function generateIdempotencyKey(): string {
  if (typeof crypto !== "undefined" && "randomUUID" in crypto) {
    return crypto.randomUUID();
  }
  return `key-${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

const initialState = {
  status: "idle" as VoiceSessionStatus,
  interimTranscript: "",
  finalTranscript: "",
  parsedIntent: null,
  aiProvider: null,
  orderPreview: null,
  lastOrder: null,
  errorMessage: null,
  idempotencyKey: null,
};

export const useVoiceSessionStore = create<VoiceSessionState>((set) => ({
  ...initialState,

  setListening: () => set({ status: "listening", errorMessage: null }),
  setInterimTranscript: (text) => set({ interimTranscript: text }),
  setFinalTranscript: (text) => set({ finalTranscript: text, interimTranscript: "" }),
  setProcessing: () => set({ status: "processing" }),
  setParsedIntent: (intent, provider) => set({ parsedIntent: intent, aiProvider: provider }),
  setOrderPreview: (preview) =>
    set({
      status: "awaiting_confirmation",
      orderPreview: preview,
      idempotencyKey: generateIdempotencyKey(),
    }),
  setConfirming: () => set({ status: "confirming" }),
  setPlaced: (order) => set({ status: "placed", lastOrder: order, orderPreview: null }),
  setError: (message) => set({ status: "error", errorMessage: message }),
  reset: () => set({ ...initialState }),
}));
