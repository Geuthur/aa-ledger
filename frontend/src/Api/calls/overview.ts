// Third Party
import { apiErrorMessage } from "aa-geuthur-react";

// AA Ledger
import { apiClient } from "@/Api/Api";
import type { LedgerOverviewResponse } from "@/Api/schema";

// Literal on purpose: App.tsx imports the pages, so importing ProjectName here would be circular.
const API_BASE = "/ledger/api";

/** Query keys of the overview area: the owner overview. */
export const overviewQueryKeys = {
  overview: ["Overview"] as const,
};

export async function fetchOverview(): Promise<LedgerOverviewResponse> {
  const { data, error } = await apiClient.GET(`${API_BASE}/overview/`);
  if (error || !data) {
    throw new Error(apiErrorMessage(error, "Failed to load overview"));
  }
  return data;
}
