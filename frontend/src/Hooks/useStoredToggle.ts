// React
import { useCallback, useState } from "react";

function readStored(key: string, defaultValue: boolean): boolean {
  try {
    const stored = window.localStorage.getItem(key);
    return stored === null ? defaultValue : stored === "true";
  } catch {
    return defaultValue;
  }
}

/**
 * A boolean preference that is kept in the browser's localStorage.
 * @returns The current value and a function to change it
 */
export function useStoredToggle(key: string, defaultValue = false) {
  const [value, setValue] = useState(() => readStored(key, defaultValue));

  const update = useCallback(
    (next: boolean) => {
      setValue(next);
      try {
        window.localStorage.setItem(key, String(next));
      } catch {
        // Storage may be unavailable (private mode); keep the value for this page only.
      }
    },
    [key],
  );

  return [value, update] as const;
}
