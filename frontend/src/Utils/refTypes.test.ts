// Third Party
import { describe, expect, it } from "vitest";

import type { CategorySchema } from "@/Api/schema";
import { filterCategories, filterRefTypes, formatRefType, sumRefTypes } from "@/Utils/refTypes";

const rows: CategorySchema[] = [
  {
    name: "Income from Market",
    amount: 400,
    average: 0,
    average_tick: 0,
    ref_types: [
      { ref_type: "market_transaction", amount: 300, characters: [] },
      { ref_type: "brokers_fee", amount: 100, characters: [] },
    ],
  },
  {
    name: "Cost from Market",
    amount: -40,
    average: 0,
    average_tick: 0,
    ref_types: [{ ref_type: "market_transaction", amount: -40, characters: [] }],
  },
  {
    name: "Income from Bounty",
    amount: 50,
    average: 0,
    average_tick: 0,
    ref_types: [{ ref_type: "bounty_prizes", amount: 50, characters: [] }],
  },
];

describe("refTypes", () => {
  it("formatRefType makes the key readable", () => {
    expect(formatRefType("market_transaction")).toBe("Market Transaction");
  });

  it("filterRefTypes ignores case and treats spaces like underscores", () => {
    // Test Action
    const result = filterRefTypes(rows[0].ref_types, "Market trans");

    // Expected Result
    expect(result.map((item) => item.ref_type)).toEqual(["market_transaction"]);
  });

  it("filterRefTypes keeps everything without a term", () => {
    expect(filterRefTypes(rows[0].ref_types, "  ")).toHaveLength(2);
  });

  it("filterCategories keeps only categories with a matching reference type", () => {
    // Test Action
    const result = filterCategories(rows, "market");

    // Expected Result
    expect(result.map((row) => row.name)).toEqual(["Income from Market", "Cost from Market"]);
  });

  it("sumRefTypes adds income and costs of a reference type", () => {
    // Test Action
    const result = sumRefTypes(rows, "market_transaction");

    // Expected Result
    expect(result).toEqual([{ ref_type: "market_transaction", amount: 260, characters: [] }]);
  });

  it("sumRefTypes sorts by the absolute amount", () => {
    // Test Action
    const result = sumRefTypes(rows, "");

    // Expected Result
    expect(result.map((item) => item.ref_type)).toEqual([
      "market_transaction",
      "brokers_fee",
      "bounty_prizes",
    ]);
  });
});
