// Third Party
import { act, renderHook } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

// AA Example
import { formatLastFetch, useLivePing } from '@/Components/Badges/liveStatusHelper';

describe('liveStatusHelper', () => {
    describe('formatLastFetch', () => {
        it('should return empty string when date is undefined or 0', () => {
            // Test Data & Test Action & Expected Result
            expect(formatLastFetch()).toBe('');
            expect(formatLastFetch(0)).toBe('');
        });

        it('should return formatted EVE time for valid timestamp', () => {
            // Test Data
            const timestamp = Date.UTC(2026, 8, 29, 12, 30, 45);

            // Test Action
            const result = formatLastFetch(timestamp);

            // Expected Result
            expect(result).toBe('12:30:45 EVE');
        });
    });

    describe('useLivePing', () => {
        beforeEach(() => {
            vi.useFakeTimers();
        });

        afterEach(() => {
            vi.useRealTimers();
        });

        it('should not ping if isBusy is true', () => {
            // Test Data & Test Action
            const { result } = renderHook(() => useLivePing(1000, true));

            // Expected Result
            expect(result.current).toBe(false);
        });

        it('should ping and reset after specified duration', () => {
            // Test Data & Test Action
            const { result } = renderHook(() => useLivePing(1000, false, 1500));

            // Expected Result: initial ping is true
            expect(result.current).toBe(true);

            // Test Action: advance timers past duration
            act(() => {
                vi.advanceTimersByTime(1600);
            });

            // Expected Result: ping reset to false
            expect(result.current).toBe(false);
        });
    });
});
