// React
import { useCallback } from "react";

// Third Party
import { parseAsInteger, parseAsStringLiteral, useQueryState, useQueryStates } from "nuqs";

import type { Section } from "@/Api/schema";

const sections = ["summary", "single"] as const satisfies readonly Section[];

const parsers = {
  details: parseAsInteger,
  section: parseAsStringLiteral(sections).withDefault("summary"),
};

/** The entity whose details are shown in the modal, kept in the URL (`?details=123&section=single`). */
export function useDetailsState() {
  const [state, setState] = useQueryStates(parsers, { clearOnDefault: true });

  const openDetails = useCallback(
    (entityId: number, section: Section = "summary") =>
      setState({ details: entityId, section }),
    [setState],
  );
  const closeDetails = useCallback(() => setState({ details: null, section: null }), [setState]);

  return { entityId: state.details, section: state.section, openDetails, closeDetails };
}

/** The selected corporation division, kept in the URL (`?division=1`). `null` means all divisions. */
export function useDivisionFilter() {
  const [division, setDivision] = useQueryState("division", parseAsInteger);
  return [division, setDivision] as const;
}
