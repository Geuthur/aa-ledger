// Third Party
import { describe, expect, it } from "vitest";

import type {
  AllianceLedgerResponse,
  CharacterLedgerResponse,
  CorporationLedgerResponse,
} from "@/Api/schema";
import { amountClass, characterRows, corporationRows, entityRows, sumRows } from "@/Utils/ledger";

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

  it("entityRows exposes the alts and flags members", () => {
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
        {
          entity: {
            entity_id: 4,
            entity_name: "NPC Corp",
            alts: [],
          },
          ledger: { bounty: 0, ess: 0, costs: 0, miscellaneous: 0, total: 0 },
        },
      ],
    } as CorporationLedgerResponse;

    // Test Action
    const rows = entityRows(response);

    // Expected Result
    expect(rows[0].alts).toHaveLength(1);
    expect(rows[0].is_member).toBe(true);
    expect(rows[0].mining).toBeUndefined();
    expect(rows[1].is_member).toBe(false);
  });

  it("corporationRows flags the user corporation as member", () => {
    // Test Data
    const response = {
      corporations: [
        {
          corporation: { entity_id: 100, entity_name: "My Corp" },
          ledger: { bounty: 10, ess: 0, costs: 0, miscellaneous: 0, total: 10 },
        },
        {
          corporation: { entity_id: 200, entity_name: "Other Corp" },
          ledger: { bounty: 20, ess: 0, costs: 0, miscellaneous: 0, total: 20 },
        },
      ],
    } as AllianceLedgerResponse;

    // Test Action
    const rows = corporationRows(response, 100);

    // Expected Result
    expect(rows[0].is_member).toBe(true);
    expect(rows[1].is_member).toBe(false);
  });

  it("returns no rows without a response", () => {
    expect(characterRows()).toEqual([]);
    expect(entityRows()).toEqual([]);
    expect(corporationRows()).toEqual([]);
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
