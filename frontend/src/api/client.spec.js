import { describe, expect, it } from "vitest";
import { apiErrorMessage } from "./client";

describe("apiErrorMessage", () => {
  it("extracts a plain string detail", () => {
    const error = { response: { data: { detail: "Incorrect email or password" } } };
    expect(apiErrorMessage(error)).toBe("Incorrect email or password");
  });

  it("joins a list of validation errors", () => {
    const error = { response: { data: { detail: [{ msg: "field required" }, { msg: "must be positive" }] } } };
    expect(apiErrorMessage(error)).toBe("field required; must be positive");
  });

  it("falls back to the default message when there is no detail", () => {
    const error = {};
    expect(apiErrorMessage(error, "fallback message")).toBe("fallback message");
  });
});
