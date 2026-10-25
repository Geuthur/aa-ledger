// React
import { useCallback, useEffect, useState } from "react";

/**
 * Counts a single cooldown down to zero, one second at a time.
 * @returns The remaining seconds and a function to start the cooldown
 */
export function useCooldown() {
  const [seconds, setSeconds] = useState(0);

  useEffect(() => {
    if (seconds <= 0) return;
    const timer = setInterval(() => {
      setSeconds((prev) => (prev > 0 ? prev - 1 : 0));
    }, 1000);
    return () => clearInterval(timer);
  }, [seconds]);

  const start = useCallback((duration: number) => setSeconds(duration), []);

  return { seconds, start };
}

/**
 * Counts one cooldown per owner id down to zero, one second at a time.
 * @returns The remaining seconds by owner id and a function to start a cooldown
 */
export function useOwnerCooldowns() {
  const [cooldowns, setCooldowns] = useState<Record<number, number>>({});

  useEffect(() => {
    const hasActive = Object.values(cooldowns).some((value) => value > 0);
    if (!hasActive) return;
    const timer = setInterval(() => {
      setCooldowns((prev) => {
        const next: Record<number, number> = {};
        for (const [key, value] of Object.entries(prev)) {
          if (value > 1) next[Number(key)] = value - 1;
        }
        return next;
      });
    }, 1000);
    return () => clearInterval(timer);
  }, [cooldowns]);

  const start = useCallback(
    (ownerId: number, duration: number) =>
      setCooldowns((prev) => ({ ...prev, [ownerId]: duration })),
    [],
  );

  return { cooldowns, start };
}
