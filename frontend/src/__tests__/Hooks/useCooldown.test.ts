// Third Party
import { act, renderHook } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

// AA Ledger
import { useCooldown, useOwnerCooldowns } from "@/Hooks/useCooldown";

describe("useCooldown", () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("should count down to zero and stop", () => {
    // Test Data
    const { result } = renderHook(() => useCooldown());

    // Test Action
    act(() => result.current.start(3));
    act(() => {
      vi.advanceTimersByTime(1000);
    });

    // Expected Result
    expect(result.current.seconds).toBe(2);
    act(() => {
      vi.advanceTimersByTime(5000);
    });
    expect(result.current.seconds).toBe(0);
  });
});

describe("useOwnerCooldowns", () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("should count each owner down and drop finished owners", () => {
    // Test Data
    const { result } = renderHook(() => useOwnerCooldowns());

    // Test Action
    act(() => result.current.start(1, 2));
    act(() => result.current.start(2, 3));
    act(() => {
      vi.advanceTimersByTime(1000);
    });

    // Expected Result
    expect(result.current.cooldowns).toEqual({ 1: 1, 2: 2 });
    act(() => {
      vi.advanceTimersByTime(1000);
    });
    expect(result.current.cooldowns).toEqual({ 2: 1 });
  });
});
