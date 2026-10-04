// Third Party
import { beforeEach, describe, expect, it, vi } from "vitest";

import { apiClient } from "@/Api/Api";
import {
  fetchAllianceDetails,
  fetchCharacterLedger,
  fetchCorporationDetails,
  fetchCorporationLedger,
  fetchPlanets,
  loadMenu,
  loadUserData,
  loadUserSettings,
  queueUpdate,
  togglePlanetNotification,
  updateUserSettings,
} from "@/Api/ApiCalls";

const ok = (data: unknown) =>
  ({ data, error: undefined, response: new Response() }) as never;
const failed = (error: unknown) =>
  ({ data: undefined, error, response: new Response() }) as never;

describe("General API client functions", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("loadUserData wraps the user", async () => {
    // Test Data
    const user = { user_id: 1, character_id: 42, character_name: "Test Pilot" };
    vi.spyOn(apiClient, "GET").mockResolvedValueOnce(ok(user));

    // Test Action
    const result = await loadUserData();

    // Expected Result
    expect(result).toEqual({ user });
    expect(apiClient.GET).toHaveBeenCalledWith("/ledger/api/user/");
  });

  it("loadUserData throws the API error message", async () => {
    // Test Data
    vi.spyOn(apiClient, "GET").mockResolvedValueOnce(failed({ error: "Permission Denied." }));

    // Test Action / Expected Result
    await expect(loadUserData()).rejects.toThrow("Permission Denied.");
  });

  it("loadMenu falls back to a generic message", async () => {
    // Test Data
    vi.spyOn(apiClient, "GET").mockResolvedValueOnce(failed({ status: 500 }));

    // Test Action / Expected Result
    await expect(loadMenu()).rejects.toThrow("Failed to load menu");
  });

  it("loadUserSettings returns the settings", async () => {
    // Test Data
    vi.spyOn(apiClient, "GET").mockResolvedValueOnce(ok({ disable_notifications: true }));

    // Test Action / Expected Result
    await expect(loadUserSettings()).resolves.toEqual({ disable_notifications: true });
    expect(apiClient.GET).toHaveBeenCalledWith("/ledger/api/settings/");
  });

  it("updateUserSettings submits the body", async () => {
    // Test Data
    vi.spyOn(apiClient, "PUT").mockResolvedValueOnce(ok({ disable_notifications: false }));

    // Test Action
    await updateUserSettings({ disable_notifications: false });

    // Expected Result
    expect(apiClient.PUT).toHaveBeenCalledWith("/ledger/api/settings/", {
      body: { disable_notifications: false },
    });
  });
});

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
    await fetchPlanets(3, true);

    // Expected Result
    expect(apiClient.GET).toHaveBeenCalledWith("/ledger/api/character/{character_id}/planets/", {
      params: { path: { character_id: 3 }, query: { single: true } },
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
});
