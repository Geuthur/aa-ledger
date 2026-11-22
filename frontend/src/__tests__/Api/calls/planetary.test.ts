// Third Party
import { beforeEach, describe, expect, it, vi } from "vitest";

// AA Ledger
import { apiClient } from "@/Api/Api";
import {
  fetchPlanetDetails,
  fetchPlanets,
  planetaryQueryKeys,
  togglePlanetNotification,
} from "@/Api/calls/planetary";

const ok = (data: unknown) =>
  ({ data, error: undefined, response: new Response() }) as never;
const failed = (error: unknown) =>
  ({ data: undefined, error, response: new Response() }) as never;

describe("planetaryQueryKeys", () => {
  it("provides the keys of the planetary area", () => {
    expect(planetaryQueryKeys.planets(3)).toEqual(["Planets", 3]);
    expect(planetaryQueryKeys.planet(3, 5)).toEqual(["PlanetDetails", 3, 5]);
  });
});

describe("Planetary API calls", () => {
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
});

type Method = "GET" | "POST";

/** Every call of `Api/calls/planetary.ts`: [name, HTTP method, call, fixed text]. */
const calls: [string, Method, () => Promise<unknown>, string][] = [
  ["fetchPlanets", "GET", () => fetchPlanets(1), "Failed to load the planets"],
  ["fetchPlanetDetails", "GET", () => fetchPlanetDetails(1, 2), "Failed to load the planet"],
  ["togglePlanetNotification", "POST", () => togglePlanetNotification(1), "Failed to toggle the notification"],
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
