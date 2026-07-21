"""Deterministic (non-AI) matching for order confirmation/cancellation phrases.

Confirmation is deliberately NOT handled by an AI provider: it gates real
side effects (placing an order), so it must be matched by an exact,
auditable phrase list rather than a model's judgement.
"""

from __future__ import annotations

import re

CONFIRM_PHRASES = {
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
}

REJECT_PHRASES = {
    "cancel",
    "cancel karo",
    "nahi",
    "nahi cancel karo",
    "no",
    "reject",
    "stop",
    "ruk jao",
}


def _normalize(text: str) -> str:
    return re.sub(r"[^\w\s]", "", text.strip().lower())


def is_confirmation_phrase(text: str) -> bool:
    return _normalize(text) in CONFIRM_PHRASES


def is_rejection_phrase(text: str) -> bool:
    return _normalize(text) in REJECT_PHRASES
