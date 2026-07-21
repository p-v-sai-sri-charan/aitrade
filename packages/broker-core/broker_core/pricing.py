"""Shared charge calculation, used both for order previews (estimates) and
actual fills, so the number a user confirms matches what they get charged.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PaperBrokerConfig:
    slippage_bps: float = 5.0  # basis points applied to market orders
    brokerage_flat: float = 20.0  # flat fee per filled order (INR)
    stt_rate_sell: float = 0.00025  # securities transaction tax, sell side
    gst_rate: float = 0.18  # GST on brokerage


def compute_charges(side: str, value: float, config: PaperBrokerConfig) -> tuple[float, float]:
    """Returns (brokerage, taxes), both rounded to 2 decimal places."""
    brokerage = config.brokerage_flat
    stt = value * config.stt_rate_sell if side == "SELL" else 0.0
    gst = brokerage * config.gst_rate
    taxes = round(stt + gst, 2)
    return round(brokerage, 2), taxes
