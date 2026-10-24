import { describe, expect, it } from "vitest";
import { mount } from "@vue/test-utils";
import RiskBadge from "./RiskBadge.vue";

describe("RiskBadge", () => {
  it("renders the risk level label in uppercase", () => {
    const wrapper = mount(RiskBadge, { props: { level: "high" } });
    expect(wrapper.text()).toContain("HIGH");
  });

  it("falls back to UNASSESSED when no level is given", () => {
    const wrapper = mount(RiskBadge, { props: { level: null } });
    expect(wrapper.text()).toContain("UNASSESSED");
  });

  function hexToRgb(hex) {
    const n = parseInt(hex.slice(1), 16);
    return `rgb(${(n >> 16) & 255}, ${(n >> 8) & 255}, ${n & 255})`;
  }

  it.each([
    ["low", "#2f9e44"],
    ["moderate", "#e8a400"],
    ["high", "#e8590c"],
    ["critical", "#c92a2a"],
  ])("colors %s risk distinctly from other levels", (level, expectedColor) => {
    const wrapper = mount(RiskBadge, { props: { level } });
    const dot = wrapper.find(".badge-dot");
    expect(dot.attributes("style")).toContain(hexToRgb(expectedColor));
  });

  it("gives each risk level a visually distinct color", () => {
    const levels = ["low", "moderate", "high", "critical"];
    const colors = levels.map((level) => mount(RiskBadge, { props: { level } }).find(".badge-dot").attributes("style"));
    expect(new Set(colors).size).toBe(levels.length);
  });
});
