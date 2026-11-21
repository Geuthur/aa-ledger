// Third Party
import { apiErrorMessage } from "aa-geuthur-react";

// AA Ledger
import { apiClient } from "@/Api/Api";
import type {
  AllianceLedgerResponse,
  CharacterLedgerResponse,
  CorporationFilterParams,
  CorporationLedgerResponse,
  DateFilterParams,
  LedgerDetailsResponse,
  Section,
} from "@/Api/schema";

// Literal on purpose: App.tsx imports the pages, so importing ProjectName here would be circular.
const API_BASE = "/ledger/api";

/** Query keys of the ledger area: ledgers and their details per owner type. */
export const ledgerQueryKeys = {
  character: (characterId: number, filters: DateFilterParams) =>
    ["CharacterLedger", characterId, filters] as const,
  corporation: (corporationId: number, filters: CorporationFilterParams) =>
    ["CorporationLedger", corporationId, filters] as const,
  alliance: (allianceId: number, filters: DateFilterParams) =>
    ["AllianceLedger", allianceId, filters] as const,
  characterDetails: (characterId: number, filters: DateFilterParams, section: Section) =>
    ["CharacterDetails", characterId, filters, section] as const,
  corporationDetails: (
    corporationId: number,
    entityId: number,
    filters: CorporationFilterParams,
    section: Section,
  ) => ["CorporationDetails", corporationId, entityId, filters, section] as const,
  allianceDetails: (
    allianceId: number,
    entityId: number,
    filters: DateFilterParams,
    section: Section,
  ) => ["AllianceDetails", allianceId, entityId, filters, section] as const,
};

export async function fetchCharacterLedger(
  characterId: number,
  filters: DateFilterParams,
): Promise<CharacterLedgerResponse> {
  const { data, error } = await apiClient.GET(`${API_BASE}/character/{character_id}/ledger/`, {
    params: { path: { character_id: characterId }, query: filters },
  });
  if (error || !data) {
    throw new Error(apiErrorMessage(error, "Failed to load the character ledger"));
  }
  return data;
}

export async function fetchCorporationLedger(
  corporationId: number,
  filters: CorporationFilterParams,
): Promise<CorporationLedgerResponse> {
  const { data, error } = await apiClient.GET(
    `${API_BASE}/corporation/{corporation_id}/ledger/`,
    { params: { path: { corporation_id: corporationId }, query: filters } },
  );
  if (error || !data) {
    throw new Error(apiErrorMessage(error, "Failed to load the corporation ledger"));
  }
  return data;
}

export async function fetchAllianceLedger(
  allianceId: number,
  filters: DateFilterParams,
): Promise<AllianceLedgerResponse> {
  const { data, error } = await apiClient.GET(`${API_BASE}/alliance/{alliance_id}/ledger/`, {
    params: { path: { alliance_id: allianceId }, query: filters },
  });
  if (error || !data) {
    throw new Error(apiErrorMessage(error, "Failed to load the alliance ledger"));
  }
  return data;
}

export async function fetchCharacterDetails(
  characterId: number,
  filters: DateFilterParams,
  section: Section,
): Promise<LedgerDetailsResponse> {
  const { data, error } = await apiClient.GET(`${API_BASE}/character/{character_id}/details/`, {
    params: { path: { character_id: characterId }, query: { ...filters, section } },
  });
  if (error || !data) {
    throw new Error(apiErrorMessage(error, "Failed to load the details"));
  }
  return data;
}

export async function fetchCorporationDetails(
  corporationId: number,
  entityId: number,
  filters: CorporationFilterParams,
  section: Section,
): Promise<LedgerDetailsResponse> {
  const { data, error } = await apiClient.GET(
    `${API_BASE}/corporation/{corporation_id}/details/`,
    {
      params: {
        path: { corporation_id: corporationId },
        query: { ...filters, entity_id: entityId, section },
      },
    },
  );
  if (error || !data) {
    throw new Error(apiErrorMessage(error, "Failed to load the details"));
  }
  return data;
}

export async function fetchAllianceDetails(
  allianceId: number,
  entityId: number,
  filters: DateFilterParams,
  section: Section,
): Promise<LedgerDetailsResponse> {
  const { data, error } = await apiClient.GET(`${API_BASE}/alliance/{alliance_id}/details/`, {
    params: {
      path: { alliance_id: allianceId },
      query: { ...filters, entity_id: entityId, section },
    },
  });
  if (error || !data) {
    throw new Error(apiErrorMessage(error, "Failed to load the details"));
  }
  return data;
}
