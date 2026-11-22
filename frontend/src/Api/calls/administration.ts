// Third Party
import { apiErrorMessage } from "aa-geuthur-react";

// AA Ledger
import { apiClient } from "@/Api/Api";
import type {
  AdministrationOwnerSchema,
  AdministrationOwnerUpdateRequest,
  AdminUpdateRequest,
  MessageSchema,
} from "@/Api/schema";

// Literal on purpose: App.tsx imports the pages, so importing ProjectName here would be circular.
const API_BASE = "/ledger/api";

/** Query keys of the administration area: all owners. */
export const administrationQueryKeys = {
  owners: ["AdministrationOwners"] as const,
};

export async function queueUpdate(request: AdminUpdateRequest): Promise<MessageSchema> {
  const { data, error } = await apiClient.POST(`${API_BASE}/admin/update/`, {
    body: request,
  });
  if (error || !data) {
    throw new Error(apiErrorMessage(error, "Failed to queue the update"));
  }
  return data;
}

export async function loadAdministrationOwners(): Promise<AdministrationOwnerSchema[]> {
  const { data, error } = await apiClient.GET(`${API_BASE}/administration/owners/`);
  if (error || !data) {
    throw new Error(apiErrorMessage(error, "Failed to load administration owners"));
  }
  return data;
}

export async function triggerAdministrationOwnerUpdate(
  ownerType: "character" | "corporation",
  ownerId: number,
  request: AdministrationOwnerUpdateRequest = { force_refresh: false },
): Promise<MessageSchema> {
  const { data, error } = await apiClient.POST(
    `${API_BASE}/administration/owners/{owner_type}/{owner_id}/update/`,
    {
      params: { path: { owner_type: ownerType, owner_id: ownerId } },
      body: request,
    },
  );
  if (error || !data) {
    throw new Error(apiErrorMessage(error, "Failed to trigger owner update"));
  }
  return data;
}

export async function deleteAdministrationOwner(
  ownerType: "character" | "corporation",
  ownerId: number,
): Promise<MessageSchema> {
  const { data, error } = await apiClient.DELETE(
    `${API_BASE}/administration/owners/{owner_type}/{owner_id}/`,
    {
      params: { path: { owner_type: ownerType, owner_id: ownerId } },
    },
  );
  if (error || !data) {
    throw new Error(apiErrorMessage(error, "Failed to delete owner"));
  }
  return data;
}
