// Third Party
import { beforeEach, describe, expect, it, vi } from "vitest";

// AA Ledger
import { apiClient } from "@/Api/Api";
import {
  fetchAllianceDetails,
  fetchAllianceLedger,
  fetchCharacterDetails,
  fetchCharacterLedger,
  fetchCorporationDetails,
  fetchCorporationLedger,
  ledgerQueryKeys,
} from "@/Api/calls/ledger";

const ok = (data: unknown) =>
  ({ data, error: undefined, response: new Response() }) as never;
const failed = (error: unknown) =>
  ({ data: undefined, error, response: new Response() }) as never;

describe("ledgerQueryKeys", () => {
  it("provides the keys of the ledger area", () => {
    expect(ledgerQueryKeys.character(1, { year: 2026 })).toEqual(["CharacterLedger", 1, { year: 2026 }]);
    expect(ledgerQueryKeys.corporation(2, { year: 2026, division_id: 3 })).toEqual([
      "CorporationLedger",
      2,
      { year: 2026, division_id: 3 },
    ]);
    expect(ledgerQueryKeys.alliance(3, { year: 2026 })).toEqual(["AllianceLedger", 3, { year: 2026 }]);
    expect(ledgerQueryKeys.characterDetails(1, { year: 2026 }, "summary")).toEqual([
      "CharacterDetails",
      1,
      { year: 2026 },
      "summary",
    ]);
    expect(ledgerQueryKeys.corporationDetails(2, 5, { year: 2026 }, "single")).toEqual([
      "CorporationDetails",
      2,
      5,
      { year: 2026 },
      "single",
    ]);
    expect(ledgerQueryKeys.allianceDetails(3, 6, { year: 2026 }, "summary")).toEqual([
      "AllianceDetails",
      3,
      6,
      { year: 2026 },
      "summary",
    ]);
  });
});

describe("Ledger API calls", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("fetchCharacterLedger sends the date as query parameters", async () => {
    // Test Data
    vi.spyOn(apiClient, "GET").mockResolvedValueOnce(ok({ characters: [] }));

    // Test Action
    await fetchCharacterLedger(7, { year: 2026, month: 10 });

    // Expected Result
    expect(apiClient.GET).toHaveBeenCalledWith("/ledger/api/character/{character_id}/ledger/", {
      params: { path: { character_id: 7 }, query: { year: 2026, month: 10 } },
    });
  });

  it("fetchCorporationLedger sends the division", async () => {
    // Test Data
    vi.spyOn(apiClient, "GET").mockResolvedValueOnce(ok({ entities: [] }));

    // Test Action
    await fetchCorporationLedger(9, { year: 2026, division_id: 2 });

    // Expected Result
    expect(apiClient.GET).toHaveBeenCalledWith(
      "/ledger/api/corporation/{corporation_id}/ledger/",
      { params: { path: { corporation_id: 9 }, query: { year: 2026, division_id: 2 } } },
    );
  });

  it("fetchCorporationDetails adds entity and section", async () => {
    // Test Data
    vi.spyOn(apiClient, "GET").mockResolvedValueOnce(ok({ summary: [] }));

    // Test Action
    await fetchCorporationDetails(9, 5, { year: 2026 }, "single");

    // Expected Result
    expect(apiClient.GET).toHaveBeenCalledWith(
      "/ledger/api/corporation/{corporation_id}/details/",
      {
        params: {
          path: { corporation_id: 9 },
          query: { year: 2026, entity_id: 5, section: "single" },
        },
      },
    );
  });

  it("fetchAllianceDetails throws the API error message", async () => {
    // Test Data
    vi.spyOn(apiClient, "GET").mockResolvedValueOnce(
      failed({ error: "You do not have permission to view this alliance." }),
    );

    // Test Action / Expected Result
    await expect(fetchAllianceDetails(1, 1, { year: 2026 }, "summary")).rejects.toThrow(
      "You do not have permission to view this alliance.",
    );
  });
});

type Method = "GET";

/** Every call of `Api/calls/ledger.ts`: [name, HTTP method, call, fixed text]. */
const calls: [string, Method, () => Promise<unknown>, string][] = [
  ["fetchCharacterLedger", "GET", () => fetchCharacterLedger(1, { year: 2026 }), "Failed to load the character ledger"],
  ["fetchCorporationLedger", "GET", () => fetchCorporationLedger(1, { year: 2026 }), "Failed to load the corporation ledger"],
  ["fetchAllianceLedger", "GET", () => fetchAllianceLedger(1, { year: 2026 }), "Failed to load the alliance ledger"],
  ["fetchCharacterDetails", "GET", () => fetchCharacterDetails(1, { year: 2026 }, "summary"), "Failed to load the details"],
  [
    "fetchCorporationDetails",
    "GET",
    () => fetchCorporationDetails(1, 2, { year: 2026 }, "summary"),
    "Failed to load the details",
  ],
  ["fetchAllianceDetails", "GET", () => fetchAllianceDetails(1, 2, { year: 2026 }, "summary"), "Failed to load the details"],
];

describe("API error messages", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  describe.each(calls)("%s", (_name, method, call, fixedText) => {
    it("should throw the message of the API when the request fails", async () => {
      // Test Data
      vi.spyOn(apiClient, method).mockResolvedValueOnce(failed({ error: "Permission Denied" }));

      // Test Action & Expected Result
      await expect(call()).rejects.toThrow("Permission Denied");
    });

    it("should throw the fixed text when the API sent no message", async () => {
      // Test Data
      vi.spyOn(apiClient, method).mockResolvedValueOnce(failed({}));

      // Test Action & Expected Result
      await expect(call()).rejects.toThrow(fixedText);
    });
  });
});
