// Third Party
import { beforeEach, describe, expect, it, vi } from "vitest";

// AA Ledger
import { apiClient } from "@/Api/Api";
import {
  administrationQueryKeys,
  deleteAdministrationOwner,
  loadAdministrationOwners,
  queueUpdate,
  triggerAdministrationOwnerUpdate,
} from "@/Api/calls/administration";

const ok = (data: unknown) =>
  ({ data, error: undefined, response: new Response() }) as never;
const failed = (error: unknown) =>
  ({ data: undefined, error, response: new Response() }) as never;

describe("administrationQueryKeys", () => {
  it("provides the keys of the administration area", () => {
    expect(administrationQueryKeys.owners).toEqual(["AdministrationOwners"]);
  });
});

describe("Administration API calls", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("triggerAdministrationOwnerUpdate sends owner and request", async () => {
    // Test Data
    vi.spyOn(apiClient, "POST").mockResolvedValueOnce(ok({ message: "queued" }));

    // Test Action
    await triggerAdministrationOwnerUpdate("corporation", 5);

    // Expected Result
    expect(apiClient.POST).toHaveBeenCalledWith(
      "/ledger/api/administration/owners/{owner_type}/{owner_id}/update/",
      {
        params: { path: { owner_type: "corporation", owner_id: 5 } },
        body: { force_refresh: false },
      },
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

type Method = "GET" | "POST" | "DELETE";

/** Every call of `Api/calls/administration.ts`: [name, HTTP method, call, fixed text]. */
const calls: [string, Method, () => Promise<unknown>, string][] = [
  ["queueUpdate", "POST", () => queueUpdate({ target: "characters", force_refresh: true }), "Failed to queue the update"],
  ["loadAdministrationOwners", "GET", () => loadAdministrationOwners(), "Failed to load administration owners"],
  [
    "triggerAdministrationOwnerUpdate",
    "POST",
    () => triggerAdministrationOwnerUpdate("character", 1),
    "Failed to trigger owner update",
  ],
  ["deleteAdministrationOwner", "DELETE", () => deleteAdministrationOwner("character", 1), "Failed to delete owner"],
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
