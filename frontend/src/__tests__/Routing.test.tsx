// Third Party
import { createQueryClient } from "aa-geuthur-react";
import { describe, expect, it, vi } from "vitest";

// The retry rule itself (network errors and 502/503/504 only) is tested in aa-geuthur-react.
vi.mock("aa-geuthur-react", async (importOriginal) => {
  const actual = await importOriginal<typeof import("aa-geuthur-react")>();
  return { ...actual, createQueryClient: vi.fn(actual.createQueryClient) };
});

describe("Routing", () => {
  it("creates the QueryClient with createQueryClient, so 4xx answers are not retried", async () => {
    await import("@/Routing");

    expect(createQueryClient).toHaveBeenCalledOnce();
  });
});
