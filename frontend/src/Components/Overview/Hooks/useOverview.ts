// Third Party
import { useQuery } from "@tanstack/react-query";

// AA Ledger
import { fetchOverview, overviewQueryKeys } from "@/Api/calls/overview";

/** Loads all owners shown on the overview page. */
export function useOverview() {
  return useQuery({
    queryKey: overviewQueryKeys.overview,
    queryFn: fetchOverview,
  });
}
