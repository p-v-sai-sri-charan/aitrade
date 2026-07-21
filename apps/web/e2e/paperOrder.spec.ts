import { expect, test } from "@playwright/test";

/**
 * End-to-end coverage of the confirmed-paper-order flow: type a command,
 * see the parsed order + risk summary, confirm it, and see the final
 * status. The backend is mocked at the network boundary so this test is
 * self-contained and deterministic -- it does not require Postgres or a
 * live AI provider to run.
 */
test("user can type a command, review the order summary, and confirm a paper order", async ({ page }) => {
  await page.route("**/api/v1/intent/parse", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        intent: {
          intent: "PLACE_ORDER",
          exchange: "NSE",
          symbol: "RELIANCE",
          side: "BUY",
          quantity: 10,
          orderType: "MARKET",
          limitPrice: null,
          product: "DELIVERY",
          validity: "DAY",
          language: "hinglish",
          confidence: 0.92,
          missingFields: [],
          requiresConfirmation: true,
          ambiguousSymbolCandidates: [],
          orderId: null,
        },
        provider: "mock",
      }),
    });
  });

  await page.route("**/api/v1/orders/preview", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        previewId: "preview-e2e-1",
        companyName: "Reliance Industries Ltd",
        request: {
          exchange: "NSE",
          symbol: "RELIANCE",
          side: "BUY",
          quantity: 10,
          orderType: "MARKET",
          limitPrice: null,
          product: "DELIVERY",
          validity: "DAY",
        },
        estimatedPrice: 2955.5,
        estimatedValue: 29555,
        estimatedBrokerage: 20,
        estimatedTaxes: 3.6,
        estimatedTotal: 29578.6,
        riskCheck: {
          allowed: true,
          code: "OK",
          message: "All risk checks passed.",
          requiresOverride: false,
        },
        expiresAt: new Date(Date.now() + 120_000).toISOString(),
      }),
    });
  });

  await page.route("**/api/v1/orders/confirm", async (route) => {
    const now = new Date().toISOString();
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        id: "order-e2e-1",
        exchange: "NSE",
        symbol: "RELIANCE",
        companyName: "Reliance Industries Ltd",
        side: "BUY",
        quantity: 10,
        filledQuantity: 10,
        orderType: "MARKET",
        limitPrice: null,
        averageFillPrice: 2955.5,
        product: "DELIVERY",
        validity: "DAY",
        status: "FILLED",
        brokerage: 20,
        taxes: 3.6,
        rejectionReason: null,
        createdAt: now,
        updatedAt: now,
      }),
    });
  });

  await page.goto("/voice");

  await expect(page.getByRole("heading", { name: "Voice Trade" })).toBeVisible();

  await page.getByPlaceholder("Or type a command...").fill("Reliance ke 10 shares market price par buy karo.");
  await page.getByRole("button", { name: "Send" }).click();

  await expect(page.getByText("Order summary")).toBeVisible();
  await expect(page.getByText("Reliance Industries Ltd")).toBeVisible();
  await expect(page.getByText("All risk checks passed.")).toBeVisible();

  const confirmButton = page.getByRole("button", { name: /confirm buy/i });
  await expect(confirmButton).toBeEnabled();
  await confirmButton.click();

  await expect(page.getByText("Order status")).toBeVisible();
  await expect(page.getByText(/FILLED.*BUY 10 RELIANCE/)).toBeVisible();
});
