// React
import type { ReactNode } from "react";

// Third Party
import { act, renderHook } from "@testing-library/react";
import { NuqsTestingAdapter } from "nuqs/adapters/testing";
import { describe, expect, it, vi } from "vitest";

import { useDateFilter } from "@/Hooks/useDateFilter";

const wrapper =
  (searchParams: string, onUrlUpdate?: (search: string) => void) =>
  ({ children }: { children: ReactNode }) => (
    <NuqsTestingAdapter
      searchParams={searchParams}
      onUrlUpdate={({ queryString }) => onUrlUpdate?.(queryString)}
    >
      {children}
    </NuqsTestingAdapter>
  );

describe("useDateFilter", () => {
  it("reads year, month and day from the URL", () => {
    // Test Action
    const { result } = renderHook(() => useDateFilter(), {
      wrapper: wrapper("?year=2024&month=6&day=29"),
    });

    // Expected Result
    expect(result.current.filters).toEqual({ year: 2024, month: 6, day: 29 });
  });

  it("defaults to the current month", () => {
    // Test Data
    const now = new Date();

    // Test Action
    const { result } = renderHook(() => useDateFilter(), { wrapper: wrapper("") });

    // Expected Result
    expect(result.current.filters).toEqual({
      year: now.getFullYear(),
      month: now.getMonth() + 1,
    });
  });

  it("treats month=0 as the whole year and ignores the day", () => {
    // Test Action
    const { result } = renderHook(() => useDateFilter(), {
      wrapper: wrapper("?year=2024&month=0&day=3"),
    });

    // Expected Result
    expect(result.current.month).toBeNull();
    expect(result.current.filters).toEqual({ year: 2024 });
  });

  it("clears the day when the month changes", async () => {
    // Test Data
    const onUrlUpdate = vi.fn();
    const { result } = renderHook(() => useDateFilter(), {
      wrapper: wrapper("?year=2024&month=6&day=29", onUrlUpdate),
    });

    // Test Action
    await act(async () => {
      await result.current.setMonth(7);
    });

    // Expected Result
    expect(onUrlUpdate).toHaveBeenCalledWith(expect.not.stringContaining("day="));
    expect(onUrlUpdate).toHaveBeenCalledWith(expect.stringContaining("month=7"));
  });
});
