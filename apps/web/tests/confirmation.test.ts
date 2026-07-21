import { describe, expect, it } from "vitest";
import { isConfirmationPhrase, isRejectionPhrase } from "../src/lib/confirmation";

describe("isConfirmationPhrase", () => {
  it.each(["confirm", "Confirm buy", "haan confirm", "order confirm karo", "Confirm Sell"])(
    "matches %s",
    (phrase) => {
      expect(isConfirmationPhrase(phrase)).toBe(true);
    },
  );

  it("does not match vague phrases", () => {
    expect(isConfirmationPhrase("ok maybe")).toBe(false);
    expect(isConfirmationPhrase("buy reliance")).toBe(false);
    expect(isConfirmationPhrase("")).toBe(false);
  });
});

describe("isRejectionPhrase", () => {
  it.each(["cancel", "nahi", "no", "stop"])("matches %s", (phrase) => {
    expect(isRejectionPhrase(phrase)).toBe(true);
  });

  it("does not match confirmation phrases", () => {
    expect(isRejectionPhrase("confirm")).toBe(false);
  });
});
