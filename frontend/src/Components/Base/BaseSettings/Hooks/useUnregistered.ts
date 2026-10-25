// Third Party
import { useQuery } from "@tanstack/react-query";

// AA Ledger
import { loadSettingsUnregistered } from "@/Api/ApiCalls";
import { queryKeys } from "@/Api/query";

/**
 * Loads the unregistered entries (characters of a corporation, corporations of an alliance).
 * Stays disabled while no owner is selected.
 */
export function useUnregistered(ownerType: string | null, ownerId: number | null) {
  return useQuery({
    queryKey: queryKeys.SettingsUnregistered(ownerType ?? "", ownerId ?? 0),
    queryFn: () => loadSettingsUnregistered(ownerType!, ownerId!),
    enabled: ownerType !== null && ownerId !== null,
  });
}
