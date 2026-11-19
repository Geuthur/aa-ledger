// Third Party
import { beforeEach, describe, expect, it, vi } from "vitest";

// AA Ledger
import { apiClient } from "@/Api/Api";
import {
  deleteAdministrationOwner,
  deleteSettingsOwner,
  fetchAllianceDetails,
  fetchAllianceLedger,
  fetchAllianceOverview,
  fetchCharacterDetails,
  fetchCharacterLedger,
  fetchCharacterOverview,
  fetchCorporationDetails,
  fetchCorporationLedger,
  fetchCorporationOverview,
  fetchOverview,
  fetchPlanetaryOverview,
  fetchPlanetDetails,
  fetchPlanets,
  loadAdministrationOwnerInspect,
  loadAdministrationOwners,
  loadSettingsOwners,
  loadSettingsUnregistered,
  queueUpdate,
  togglePlanetNotification,
  triggerAdministrationOwnerUpdate,
  triggerSettingsOwnerUpdate,
  triggerUpdateAllSettingsOwners,
} from "@/Api/ApiCalls";

const ok = (data: unknown) =>
  ({ data, error: undefined, response: new Response() }) as never;
const failed = (error: unknown) =>
  ({ data: undefined, error, response: new Response() }) as never;

describe("Ledger API client functions", () => {
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

describe("Planetary and administration API client functions", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("fetchPlanets sends single", async () => {
    // Test Data
    vi.spyOn(apiClient, "GET").mockResolvedValueOnce(ok([]));

    // Test Action
    await fetchPlanets(3);

    // Expected Result
    expect(apiClient.GET).toHaveBeenCalledWith("/ledger/api/character/{character_id}/planets/", {
      params: { path: { character_id: 3 } },
    });
  });

  it("togglePlanetNotification omits the planet to toggle all", async () => {
    // Test Data
    vi.spyOn(apiClient, "POST").mockResolvedValueOnce(
      ok({ message: "ok", notification: true }),
    );

    // Test Action
    await togglePlanetNotification(3);

    // Expected Result
    expect(apiClient.POST).toHaveBeenCalledWith(
      "/ledger/api/character/{character_id}/planets/notification/",
      { params: { path: { character_id: 3 }, query: {} } },
    );
  });

  it("queueUpdate posts the request", async () => {
    // Test Data
    vi.spyOn(apiClient, "POST").mockResolvedValueOnce(ok({ message: "queued" }));

    // Test Action
    await queueUpdate({ target: "characters", force_refresh: true });

    // Expected Result
    expect(apiClient.POST).toHaveBeenCalledWith("/ledger/api/admin/update/", {
      body: { target: "characters", force_refresh: true },
    });
  });

  it("loadSettingsUnregistered fetches unregistered entries of an owner", async () => {
    // Test Data
    const mock = { owner_type: "corporation", owner_id: 10, items: [] };
    vi.spyOn(apiClient, "GET").mockResolvedValueOnce(ok(mock));

    // Test Action
    const result = await loadSettingsUnregistered("corporation", 10);

    // Expected Result
    expect(result).toEqual(mock);
    expect(apiClient.GET).toHaveBeenCalledWith(
      "/ledger/api/settings/owners/{owner_type}/{owner_id}/unregistered/",
      { params: { path: { owner_type: "corporation", owner_id: 10 } } },
    );
  });

  it("loadSettingsOwners fetches settings owners", async () => {
    // Test Data
    const mockOwners = { registered: [], missing: [], can_update: true, cooldown_seconds: 0 };
    vi.spyOn(apiClient, "GET").mockResolvedValueOnce(ok(mockOwners));

    // Test Action
    const result = await loadSettingsOwners();

    // Expected Result
    expect(result).toEqual(mockOwners);
    expect(apiClient.GET).toHaveBeenCalledWith("/ledger/api/settings/owners/");
  });

  it("triggerUpdateAllSettingsOwners triggers update all", async () => {
    // Test Data
    vi.spyOn(apiClient, "POST").mockResolvedValueOnce(ok({ message: "Update queued" }));

    // Test Action
    const result = await triggerUpdateAllSettingsOwners();

    // Expected Result
    expect(result).toEqual({ message: "Update queued" });
    expect(apiClient.POST).toHaveBeenCalledWith("/ledger/api/settings/owners/update-all/");
  });

  it("triggerSettingsOwnerUpdate triggers single owner update", async () => {
    // Test Data
    vi.spyOn(apiClient, "POST").mockResolvedValueOnce(ok({ message: "Owner update initiated" }));

    // Test Action
    const result = await triggerSettingsOwnerUpdate("character", 123);

    // Expected Result
    expect(result).toEqual({ message: "Owner update initiated" });
    expect(apiClient.POST).toHaveBeenCalledWith(
      "/ledger/api/settings/owners/{owner_type}/{owner_id}/update/",
      { params: { path: { owner_type: "character", owner_id: 123 } } },
    );
  });

  it("deleteSettingsOwner deletes an owner", async () => {
    // Test Data
    vi.spyOn(apiClient, "DELETE").mockResolvedValueOnce(ok({ message: "Deleted" }));

    // Test Action
    const result = await deleteSettingsOwner("character", 123);

    // Expected Result
    expect(result).toEqual({ message: "Deleted" });
    expect(apiClient.DELETE).toHaveBeenCalledWith(
      "/ledger/api/settings/owners/{owner_type}/{owner_id}/",
      { params: { path: { owner_type: "character", owner_id: 123 } } },
    );
  });
});


type Method = "GET" | "POST" | "DELETE";

/** Every call of `ApiCalls.ts`: [name, HTTP method, call, fixed text]. */
const calls: [string, Method, () => Promise<unknown>, string][] = [
  ["fetchOverview", "GET", () => fetchOverview(), "Failed to load overview"],
  ["fetchCharacterOverview", "GET", () => fetchCharacterOverview(), "Failed to load characters"],
  ["fetchPlanetaryOverview", "GET", () => fetchPlanetaryOverview(), "Failed to load characters"],
  ["fetchCorporationOverview", "GET", () => fetchCorporationOverview(), "Failed to load corporations"],
  ["fetchAllianceOverview", "GET", () => fetchAllianceOverview(), "Failed to load alliances"],
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
  ["fetchPlanets", "GET", () => fetchPlanets(1), "Failed to load the planets"],
  ["fetchPlanetDetails", "GET", () => fetchPlanetDetails(1, 2), "Failed to load the planet"],
  ["togglePlanetNotification", "POST", () => togglePlanetNotification(1), "Failed to toggle the notification"],
  ["queueUpdate", "POST", () => queueUpdate({ target: "characters", force_refresh: true }), "Failed to queue the update"],
  ["loadAdministrationOwners", "GET", () => loadAdministrationOwners(), "Failed to load administration owners"],
  [
    "triggerAdministrationOwnerUpdate",
    "POST",
    () => triggerAdministrationOwnerUpdate("character", 1),
    "Failed to trigger owner update",
  ],
  ["deleteAdministrationOwner", "DELETE", () => deleteAdministrationOwner("character", 1), "Failed to delete owner"],
  [
    "loadAdministrationOwnerInspect",
    "GET",
    () => loadAdministrationOwnerInspect("character", 1),
    "Failed to inspect owner",
  ],
  ["loadSettingsOwners", "GET", () => loadSettingsOwners(), "Failed to load settings owners"],
  ["triggerUpdateAllSettingsOwners", "POST", () => triggerUpdateAllSettingsOwners(), "Failed to trigger update all"],
  ["triggerSettingsOwnerUpdate", "POST", () => triggerSettingsOwnerUpdate("character", 1), "Failed to update owner"],
  [
    "loadSettingsUnregistered",
    "GET",
    () => loadSettingsUnregistered("character", 1),
    "Failed to load unregistered entries",
  ],
  ["deleteSettingsOwner", "DELETE", () => deleteSettingsOwner("character", 1), "Failed to delete owner"],
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
