import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import type { OrderPreview } from "@vaanitrade/shared-types";
import { OrderSummaryCard } from "../src/components/voice/OrderSummaryCard";

const basePreview: OrderPreview = {
  previewId: "preview-1",
  companyName: "Reliance Industries Ltd",
  request: {
    exchange: "NSE",
    symbol: "RELIANCE",
    side: "BUY",
    quantity: 10,
    orderType: "LIMIT",
    limitPrice: 2950,
    product: "DELIVERY",
    validity: "DAY",
  },
  estimatedPrice: 2950,
  estimatedValue: 29500,
  estimatedBrokerage: 20,
  estimatedTaxes: 3.6,
  estimatedTotal: 29523.6,
  riskCheck: { allowed: true, code: "OK", message: "All risk checks passed.", requiresOverride: false },
  expiresAt: new Date().toISOString(),
};

describe("OrderSummaryCard", () => {
  it("calls onConfirm when the confirm button is pressed and the order is allowed", async () => {
    const onConfirm = vi.fn();
    render(<OrderSummaryCard preview={basePreview} onConfirm={onConfirm} onCancel={vi.fn()} />);

    const confirmButton = screen.getByRole("button", { name: /confirm buy/i });
    expect(confirmButton).toBeEnabled();

    await userEvent.click(confirmButton);
    expect(onConfirm).toHaveBeenCalledOnce();
  });

  it("disables the confirm button when the risk check blocks the order", () => {
    const blockedPreview: OrderPreview = {
      ...basePreview,
      riskCheck: {
        allowed: false,
        code: "ORDER_VALUE_LIMIT_EXCEEDED",
        message: "Order value exceeds your configured limit.",
        requiresOverride: false,
      },
    };
    render(<OrderSummaryCard preview={blockedPreview} onConfirm={vi.fn()} onCancel={vi.fn()} />);

    expect(screen.getByRole("button", { name: /confirm buy/i })).toBeDisabled();
    expect(screen.getByRole("alert")).toHaveTextContent("Order value exceeds your configured limit.");
  });

  it("shows the company name and quantity", () => {
    render(<OrderSummaryCard preview={basePreview} onConfirm={vi.fn()} onCancel={vi.fn()} />);
    expect(screen.getByText("Reliance Industries Ltd")).toBeInTheDocument();
    expect(screen.getByText("10")).toBeInTheDocument();
  });
});
