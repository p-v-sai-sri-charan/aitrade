import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { RiskWarning } from "../src/components/ui/RiskWarning";

describe("RiskWarning", () => {
  it("renders a success message when the order is allowed", () => {
    render(
      <RiskWarning
        riskCheck={{ allowed: true, code: "OK", message: "All risk checks passed.", requiresOverride: false }}
      />,
    );
    expect(screen.getByRole("status")).toHaveTextContent("All risk checks passed.");
  });

  it("renders an alert with the risk code when blocked", () => {
    render(
      <RiskWarning
        riskCheck={{
          allowed: false,
          code: "ORDER_VALUE_LIMIT_EXCEEDED",
          message: "Order value exceeds your configured limit.",
          requiresOverride: false,
        }}
      />,
    );
    const alert = screen.getByRole("alert");
    expect(alert).toHaveTextContent("ORDER VALUE LIMIT EXCEEDED");
    expect(alert).toHaveTextContent("Order value exceeds your configured limit.");
  });
});
