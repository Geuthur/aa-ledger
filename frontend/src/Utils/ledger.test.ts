// Third Party
import { describe, expect, it } from "vitest";

import type { CharacterLedgerResponse, CorporationLedgerResponse } from "@/Api/schema";
import { amountClass, characterRows, entityRows, sumRows } from "@/Utils/ledger";

describe("ledger rows", () => {
  it("characterRows keeps mining out of the total", () => {
    // Test Data
    const response = {
      characters: [
        {
          character: { character_id: 1, character_name: "Alice", icon: "a.png" },
          ledger: { bounty: 100, ess: 10, costs: -20, miscellaneous: 5, total: 95, mining: 500 },
          update_status: { status: "ok" },
        },
      ],
    } as CharacterLedgerResponse;

    // Test Action
    const [row] = characterRows(response);

    // Expected Result
    expect(row).toMatchObject({ id: 1, name: "Alice", mining: 500, total: 95, status: "ok" });
  });

  it("entityRows exposes the alts", () => {
    // Test Data
    const response = {
      entities: [
        {
          entity: {
            entity_id: 2,
            entity_name: "Bob",
            alts: [{ character_id: 3, character_name: "Bob Alt" }],
          },
          ledger: { bounty: 1, ess: 0, costs: 0, miscellaneous: 0, total: 1 },
        },
      ],
    } as CorporationLedgerResponse;

    // Test Action
    const [row] = entityRows(response);

    // Expected Result
    expect(row.alts).toHaveLength(1);
    expect(row.mining).toBeUndefined();
  });

  it("returns no rows without a response", () => {
    expect(characterRows()).toEqual([]);
    expect(entityRows()).toEqual([]);
  });

  it("sumRows adds up every column", () => {
    // Test Data
    const rows = [
      { id: 1, name: "A", alts: [], bounty: 1, ess: 2, mining: 3, miscellaneous: 4, costs: -5, total: 2 },
      { id: 2, name: "B", alts: [], bounty: 10, ess: 20, miscellaneous: 40, costs: -50, total: 20 },
    ];

    // Test Action / Expected Result
    expect(sumRows(rows)).toEqual({
      bounty: 11,
      ess: 22,
      mining: 3,
      miscellaneous: 44,
      costs: -55,
      total: 22,
    });
  });

  it("amountClass colours income, costs and mining", () => {
    expect(amountClass(10)).toBe("text-success");
    expect(amountClass(-10)).toBe("text-danger");
    expect(amountClass(0)).toBe("");
    expect(amountClass(10, true)).toBe("text-info");
  });
});
