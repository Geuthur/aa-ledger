// Third Party
import { describe, expect, it } from "vitest";

import { buildChordMatrix, buildTimelineChart } from "@/Utils/billboard";

describe("buildTimelineChart", () => {
  it("returns an empty chart without data", () => {
    expect(buildTimelineChart(null)).toEqual({ categories: [], series: [] });
  });

  it("creates one series per category and fills gaps with zero", () => {
    // Test Data
    const billboard = {
      categories: [
        { name: "Bounty", label: "Bounty" },
        { name: "ESS", label: "ESS" },
      ],
      series: [
        { date: "2026-09", Bounty: 100, ESS: 20 },
        { date: "2026-10", Bounty: 50 },
      ],
    };

    // Test Action
    const chart = buildTimelineChart(billboard);

    // Expected Result
    expect(chart.categories).toEqual(["2026-09", "2026-10"]);
    expect(chart.series).toEqual([
      { name: "Bounty", data: [100, 50] },
      { name: "ESS", data: [20, 0] },
    ]);
  });
});

describe("buildChordMatrix", () => {
  it("returns an empty matrix without data", () => {
    expect(buildChordMatrix(null)).toEqual({ names: [], matrix: [] });
  });

  it("lists sources before targets and sums the flows", () => {
    // Test Data
    const billboard = {
      categories: [],
      series: [
        { from: "Alice", to: "Bounty", value: 10 },
        { from: "Alice", to: "Bounty", value: 5 },
        { from: "Bob", to: "ESS", value: 7 },
      ],
    };

    // Test Action
    const { names, matrix } = buildChordMatrix(billboard);

    // Expected Result
    expect(names).toEqual(["Alice", "Bob", "Bounty", "ESS"]);
    expect(matrix[0][2]).toBe(15);
    expect(matrix[1][3]).toBe(7);
    expect(matrix[2][0]).toBe(0);
  });
});
