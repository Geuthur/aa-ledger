// Third Party
import { useQuery } from "@tanstack/react-query";

// AA Ledger
import { loadMenu } from "@/Api/ApiCalls";
import { queryKeys } from "@/Api/query";

/** Loads the left and right menu links. */
export function useMenu() {
  return useQuery({
    queryKey: queryKeys.Menu,
    queryFn: () => loadMenu(),
    staleTime: 5 * 60 * 1000,
    retry: 1,
    refetchOnWindowFocus: false,
  });
}
