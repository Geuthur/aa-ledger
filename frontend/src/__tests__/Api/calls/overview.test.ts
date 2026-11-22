// Third Party
import { beforeEach, describe, expect, it, vi } from "vitest";

// AA Ledger
import { apiClient } from "@/Api/Api";
import { fetchOverview, overviewQueryKeys } from "@/Api/calls/overview";

const ok = (data: unknown) =>
  ({ data, error: undefined, response: new Response() }) as never;
const failed = (error: unknown) =>
  ({ data: undefined, error, response: new Response() }) as never;

describe("overviewQueryKeys", () => {
  it("provides the keys of the overview area", () => {
    expect(overviewQueryKeys.overview).toEqual(["Overview"]);
  });
});

describe("Overview API calls", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("fetchOverview returns the overview", async () => {
    // Test Data
    const mock = { owners: [] };
    vi.spyOn(apiClient, "GET").mockResolvedValueOnce(ok(mock));

    // Test Action
    const result = await fetchOverview();

    // Expected Result
    expect(result).toEqual(mock);
    expect(apiClient.GET).toHaveBeenCalledWith("/ledger/api/overview/");
  });
});

type Method = "GET";

/** Every call of `Api/calls/overview.ts`: [name, HTTP method, call, fixed text]. */
const calls: [string, Method, () => Promise<unknown>, string][] = [
  ["fetchOverview", "GET", () => fetchOverview(), "Failed to load overview"],
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
