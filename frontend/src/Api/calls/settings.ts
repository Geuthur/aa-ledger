// Third Party
import { apiErrorMessage } from "aa-geuthur-react";

// AA Ledger
import { apiClient } from "@/Api/Api";
import type {
  MessageSchema,
  SettingsOwnersResponse,
  SettingsUnregisteredResponse,
} from "@/Api/schema";

// Literal on purpose: App.tsx imports the pages, so importing ProjectName here would be circular.
const API_BASE = "/ledger/api";

/** Query keys of the settings area: the owners of the user and the unregistered entries of one owner. */
export const settingsQueryKeys = {
  owners: ["SettingsOwners"] as const,
  unregistered: (ownerType: string, ownerId: number) =>
    ["SettingsUnregistered", ownerType, ownerId] as const,
};

export async function loadSettingsOwners(): Promise<SettingsOwnersResponse> {
  const { data, error } = await apiClient.GET(`${API_BASE}/settings/owners/`);
  if (error || !data) {
    throw new Error(apiErrorMessage(error, "Failed to load settings owners"));
  }
  return data;
}

export async function triggerUpdateAllSettingsOwners(): Promise<MessageSchema> {
  const { data, error } = await apiClient.POST(`${API_BASE}/settings/owners/update-all/`);
  if (error || !data) {
    throw new Error(apiErrorMessage(error, "Failed to trigger update all"));
  }
  return data;
}

export async function triggerSettingsOwnerUpdate(
  ownerType: string,
  ownerId: number,
): Promise<MessageSchema> {
  const { data, error } = await apiClient.POST(
    `${API_BASE}/settings/owners/{owner_type}/{owner_id}/update/`,
    { params: { path: { owner_type: ownerType, owner_id: ownerId } } },
  );
  if (error || !data) {
    throw new Error(apiErrorMessage(error, "Failed to update owner"));
  }
  return data;
}

export async function loadSettingsUnregistered(
  ownerType: string,
  ownerId: number,
): Promise<SettingsUnregisteredResponse> {
  const { data, error } = await apiClient.GET(
    `${API_BASE}/settings/owners/{owner_type}/{owner_id}/unregistered/`,
    { params: { path: { owner_type: ownerType, owner_id: ownerId } } },
  );
  if (error || !data) {
    throw new Error(apiErrorMessage(error, "Failed to load unregistered entries"));
  }
  return data;
}

export async function deleteSettingsOwner(
  ownerType: string,
  ownerId: number,
): Promise<MessageSchema> {
  const { data, error } = await apiClient.DELETE(
    `${API_BASE}/settings/owners/{owner_type}/{owner_id}/`,
    { params: { path: { owner_type: ownerType, owner_id: ownerId } } },
  );
  if (error || !data) {
    throw new Error(apiErrorMessage(error, "Failed to delete owner"));
  }
  return data;
}
