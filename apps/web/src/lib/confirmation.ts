/**
 * Deterministic confirmation-phrase matching, mirroring
 * packages/ai-providers/ai_providers/confirmation.py. Confirming an order
 * is a real side effect, so it is matched by an exact phrase list -- never
 * inferred by an AI model -- and only ever applies when there is exactly
 * one pending order preview to confirm.
 */

const CONFIRM_PHRASES = new Set([
  "confirm",
  "confirm order",
  "confirm buy",
  "confirm sell",
  "yes confirm",
  "haan confirm",
  "haan confirm karo",
  "order confirm karo",
  "confirm karo",
  "confirm kar do",
  "haan kar do",
  "haan karo",
  "proceed",
  "ok confirm",
]);

const REJECT_PHRASES = new Set([
  "cancel",
  "cancel karo",
  "nahi",
  "nahi cancel karo",
  "no",
  "reject",
  "stop",
  "ruk jao",
]);

function normalize(text: string): string {
  return text
    .trim()
    .toLowerCase()
    .replace(/[^\w\s]/g, "");
}

export function isConfirmationPhrase(text: string): boolean {
  return CONFIRM_PHRASES.has(normalize(text));
}

export function isRejectionPhrase(text: string): boolean {
  return REJECT_PHRASES.has(normalize(text));
}
