// Third Party
import { useQuery } from "@tanstack/react-query";

// AA Ledger
import { loadSettingsUnregistered, settingsQueryKeys } from "@/Api/calls/settings";

/**
 * Loads the unregistered entries (characters of a corporation, corporations of an alliance).
 * Stays disabled while no owner is selected.
 */
export function useUnregistered(ownerType: string | null, ownerId: number | null) {
  return useQuery({
    queryKey: settingsQueryKeys.unregistered(ownerType ?? "", ownerId ?? 0),
    queryFn: () => loadSettingsUnregistered(ownerType!, ownerId!),
    enabled: ownerType !== null && ownerId !== null,
  });
}
