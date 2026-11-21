// Third Party
import { beforeEach, describe, expect, it, vi } from "vitest";

// AA Ledger
import { apiClient } from "@/Api/Api";
import {
  deleteSettingsOwner,
  loadSettingsOwners,
  loadSettingsUnregistered,
  settingsQueryKeys,
  triggerSettingsOwnerUpdate,
  triggerUpdateAllSettingsOwners,
} from "@/Api/calls/settings";

const ok = (data: unknown) =>
  ({ data, error: undefined, response: new Response() }) as never;
const failed = (error: unknown) =>
  ({ data: undefined, error, response: new Response() }) as never;

describe("settingsQueryKeys", () => {
  it("provides the keys of the settings area", () => {
    expect(settingsQueryKeys.owners).toEqual(["SettingsOwners"]);
    expect(settingsQueryKeys.unregistered("corporation", 10)).toEqual([
      "SettingsUnregistered",
      "corporation",
      10,
    ]);
  });
});

describe("Settings API calls", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
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

/** Every call of `Api/calls/settings.ts`: [name, HTTP method, call, fixed text]. */
const calls: [string, Method, () => Promise<unknown>, string][] = [
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
