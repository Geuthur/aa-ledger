// React
import { useEffect, useState } from "react";

const easeOutCubic = (t: number) => 1 - Math.pow(1 - t, 3);

export const prefersReducedMotion = () =>
  typeof window !== "undefined" &&
  typeof window.matchMedia === "function" &&
  window.matchMedia("(prefers-reduced-motion: reduce)").matches;

/**
 * Eased progress from 0 to 1 that starts when the component mounts.
 * Remount the component (change its `key`) to play the animation again.
 */
export function useAnimationProgress(duration = 900): number {
  const [progress, setProgress] = useState(() => (prefersReducedMotion() ? 1 : 0));

  useEffect(() => {
    if (progress === 1) return;

    let frame = 0;
    const start = performance.now();
    const tick = (now: number) => {
      const elapsed = Math.min(1, (now - start) / duration);
      setProgress(easeOutCubic(elapsed));
      if (elapsed < 1) frame = requestAnimationFrame(tick);
    };
    frame = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(frame);
    // The animation runs once per mount.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [duration]);

  return progress;
}
