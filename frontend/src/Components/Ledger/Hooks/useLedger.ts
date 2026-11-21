// Third Party
import { keepPreviousData, useQuery } from "@tanstack/react-query";
import type { QueryKey } from "@tanstack/react-query";

// AA Ledger
import {
  fetchAllianceLedger,
  fetchCharacterLedger,
  fetchCorporationLedger,
  ledgerQueryKeys,
} from "@/Api/calls/ledger";
import type {
  CorporationFilterParams,
  DateFilterParams,
  LedgerDetailsResponse,
} from "@/Api/schema";

/** Loads the ledger of a character; keeps the previous data while filters change. */
export function useCharacterLedger(characterId: number, filters: DateFilterParams) {
  return useQuery({
    queryKey: ledgerQueryKeys.character(characterId, filters),
    queryFn: () => fetchCharacterLedger(characterId, filters),
    placeholderData: keepPreviousData,
  });
}

/** Loads the ledger of a corporation; keeps the previous data while filters change. */
export function useCorporationLedger(corporationId: number, filters: CorporationFilterParams) {
  return useQuery({
    queryKey: ledgerQueryKeys.corporation(corporationId, filters),
    queryFn: () => fetchCorporationLedger(corporationId, filters),
    placeholderData: keepPreviousData,
  });
}

/** Loads the ledger of an alliance; keeps the previous data while filters change. */
export function useAllianceLedger(allianceId: number, filters: DateFilterParams) {
  return useQuery({
    queryKey: ledgerQueryKeys.alliance(allianceId, filters),
    queryFn: () => fetchAllianceLedger(allianceId, filters),
    placeholderData: keepPreviousData,
    enabled: Boolean(allianceId),
  });
}

/**
 * Loads the category details of a ledger entity.
 * @param queryKey Key of the details query (from `ledgerQueryKeys`)
 * @param queryFn Loader of the details
 * @param enabled Whether an entity is selected
 */
export function useLedgerDetails(
  queryKey: QueryKey,
  queryFn: () => Promise<LedgerDetailsResponse>,
  enabled: boolean,
) {
  return useQuery({ queryKey, queryFn, enabled });
}
