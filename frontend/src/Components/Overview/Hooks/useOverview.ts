// Third Party
import { useQuery } from "@tanstack/react-query";

// AA Ledger
import { fetchOverview } from "@/Api/ApiCalls";
import { queryKeys } from "@/Api/query";

/** Loads all owners shown on the overview page. */
export function useOverview() {
  return useQuery({
    queryKey: queryKeys.Overview,
    queryFn: fetchOverview,
  });
}
