// React
import { useCallback, useMemo } from "react";

// Third Party
import { parseAsInteger, useQueryStates } from "nuqs";

import type { DateFilterParams } from "@/Api/schema";

/** `month=0` in the URL selects the whole year, so that the current month can be the default. */
export const ALL_MONTHS = 0;

const now = new Date();

const parsers = {
  year: parseAsInteger.withDefault(now.getFullYear()),
  month: parseAsInteger.withDefault(now.getMonth() + 1),
  day: parseAsInteger,
};

/**
 * Year, month and day of the ledger, kept in the URL (`?year=2026&month=10&day=4`).
 * A day is only valid together with a month.
 */
export function useDateFilter() {
  const [state, setState] = useQueryStates(parsers, { clearOnDefault: true });

  const month = state.month === ALL_MONTHS ? null : state.month;
  const day = month === null ? null : state.day;

  const filters = useMemo<DateFilterParams>(
    () => ({
      year: state.year,
      ...(month !== null ? { month } : {}),
      ...(month !== null && day !== null ? { day } : {}),
    }),
    [state.year, month, day],
  );

  const setYear = useCallback((year: number) => setState({ year }), [setState]);
  const setMonth = useCallback(
    (value: number | null) => setState({ month: value ?? ALL_MONTHS, day: null }),
    [setState],
  );
  const setDay = useCallback((value: number | null) => setState({ day: value }), [setState]);

  return { year: state.year, month, day, filters, setYear, setMonth, setDay };
}
