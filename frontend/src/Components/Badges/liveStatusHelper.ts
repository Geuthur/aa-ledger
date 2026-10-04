// React
import { useEffect, useRef, useState } from 'react';

// Voices of War
import { formatEveTime } from '@/Utils/eveOnline';

/**
 * Formats a numeric timestamp into an EVE Online time string (HH:MM:SS EVE)
 * @param date Timestamp in milliseconds
 * @returns Formatted EVE time string
 */
export function formatLastFetch(date?: number): string {
    if (!date) return '';
    return formatEveTime(new Date(date));
}

/**
 * Hook to manage the short ping animation whenever dataUpdatedAt changes
 * @param dataUpdatedAt Timestamp of the last query fetch
 * @param isBusy True if query is currently loading or refetching
 * @param duration Duration in milliseconds of the ping animation (default: 2000)
 */
export function useLivePing(
    dataUpdatedAt?: number,
    isBusy: boolean = false,
    duration: number = 2000
): boolean {
    const [pinging, setPinging] = useState(false);
    const pingTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

    useEffect(() => {
        if (isBusy) return;

        // eslint-disable-next-line react-hooks/set-state-in-effect
        setPinging(true);
        if (pingTimer.current) clearTimeout(pingTimer.current);
        pingTimer.current = setTimeout(() => {
            setPinging(false);
        }, duration);
    }, [dataUpdatedAt, isBusy, duration]);

    return pinging;
}
