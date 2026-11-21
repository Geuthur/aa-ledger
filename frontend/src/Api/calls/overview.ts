// Third Party
import { apiErrorMessage } from "aa-geuthur-react";

// AA Ledger
import { apiClient } from "@/Api/Api";
import type {
  AllianceOverview,
  CharacterOverview,
  CorporationOverview,
  LedgerOverviewResponse,
} from "@/Api/schema";

// Literal on purpose: App.tsx imports the pages, so importing ProjectName here would be circular.
const API_BASE = "/ledger/api";

/** Query keys of the overview area: the owner overview and the overviews per owner type. */
export const overviewQueryKeys = {
  overview: ["Overview"] as const,
  character: ["CharacterOverview"] as const,
  planetary: ["PlanetaryOverview"] as const,
  corporation: ["CorporationOverview"] as const,
  alliance: ["AllianceOverview"] as const,
};

export async function fetchOverview(): Promise<LedgerOverviewResponse> {
  const { data, error } = await apiClient.GET(`${API_BASE}/overview/`);
  if (error || !data) {
    throw new Error(apiErrorMessage(error, "Failed to load overview"));
  }
  return data;
}

export async function fetchCharacterOverview(): Promise<CharacterOverview[]> {
  const { data, error } = await apiClient.GET(`${API_BASE}/character/overview/`);
  if (error || !data) {
    throw new Error(apiErrorMessage(error, "Failed to load characters"));
  }
  return data;
}

export async function fetchPlanetaryOverview(): Promise<CharacterOverview[]> {
  const { data, error } = await apiClient.GET(`${API_BASE}/planetary/overview/`);
  if (error || !data) {
    throw new Error(apiErrorMessage(error, "Failed to load characters"));
  }
  return data;
}

export async function fetchCorporationOverview(): Promise<CorporationOverview[]> {
  const { data, error } = await apiClient.GET(`${API_BASE}/corporation/overview/`);
  if (error || !data) {
    throw new Error(apiErrorMessage(error, "Failed to load corporations"));
  }
  return data;
}

export async function fetchAllianceOverview(): Promise<AllianceOverview[]> {
  const { data, error } = await apiClient.GET(`${API_BASE}/alliance/overview/`);
  if (error || !data) {
    throw new Error(apiErrorMessage(error, "Failed to load alliances"));
  }
  return data;
}
