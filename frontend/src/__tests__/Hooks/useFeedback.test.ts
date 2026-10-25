// Third Party
import { act, renderHook } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

// AA Ledger
import { useFeedback } from "@/Hooks/useFeedback";

describe("useFeedback", () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("should show the message and clear it after the timeout", () => {
    // Test Data
    const { result } = renderHook(() => useFeedback(5000));

    // Test Action
    act(() => result.current.showFeedback("success", "Saved"));

    // Expected Result
    expect(result.current.feedback).toEqual({ variant: "success", text: "Saved" });
    act(() => {
      vi.advanceTimersByTime(5000);
    });
    expect(result.current.feedback).toBeNull();
  });

  it("should restart the timeout when a new message replaces the old one", () => {
    // Test Data
    const { result } = renderHook(() => useFeedback(5000));
    act(() => result.current.showFeedback("danger", "First"));
    act(() => {
      vi.advanceTimersByTime(4000);
    });

    // Test Action
    act(() => result.current.showFeedback("success", "Second"));
    act(() => {
      vi.advanceTimersByTime(4000);
    });

    // Expected Result
    expect(result.current.feedback).toEqual({ variant: "success", text: "Second" });
  });

  it("should clear the message right away when dismissed", () => {
    // Test Data
    const { result } = renderHook(() => useFeedback());
    act(() => result.current.showFeedback("danger", "Failed"));

    // Test Action
    act(() => result.current.clearFeedback());

    // Expected Result
    expect(result.current.feedback).toBeNull();
  });
});
