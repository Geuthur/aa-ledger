import { apiClient } from "@/Api/Api";
import type {
  AdminUpdateRequest,
  AdministrationResponse,
  AllianceLedgerResponse,
  AllianceOverview,
  CharacterLedgerResponse,
  CharacterOverview,
  CorporationFilterParams,
  CorporationLedgerResponse,
  CorporationOverview,
  DateFilterParams,
  LedgerDetailsResponse,
  MenuSchema,
  MessageSchema,
  NotificationResponse,
  PlanetDetailResponse,
  PlanetaryDetails,
  Section,
  UserData,
  UserSettingsSchema,
  UserSettingsUpdateRequest,
} from "@/Api/schema";

// Literal on purpose: App.tsx imports the pages, so importing ProjectName here would be circular.
const API_BASE = "/ledger/api";

/** Prefer the message sent by the API (`{"error": "..."}`) over the generic fallback. */
function errorMessage(error: unknown, fallback: string): string {
  if (typeof error === "object" && error !== null && "error" in error) {
    const message = (error as { error: unknown }).error;
    if (typeof message === "string") return message;
  }
  return fallback;
}

export async function loadUserData(): Promise<{ user: UserData }> {
  const { data, error } = await apiClient.GET(`${API_BASE}/user/`);
  if (error || !data) {
    throw new Error(errorMessage(error, "Failed to load user data"));
  }
  return { user: data };
}

export async function loadMenu(): Promise<MenuSchema> {
  const { data, error } = await apiClient.GET(`${API_BASE}/menu/`);
  if (error || !data) {
    throw new Error(errorMessage(error, "Failed to load menu"));
  }
  return data;
}

export async function loadUserSettings(): Promise<UserSettingsSchema> {
  const { data, error } = await apiClient.GET(`${API_BASE}/settings/`);
  if (error || !data) {
    throw new Error(errorMessage(error, "Failed to load user settings"));
  }
  return data;
}

export async function updateUserSettings(
  settings: UserSettingsUpdateRequest,
): Promise<UserSettingsSchema> {
  const { data, error } = await apiClient.PUT(`${API_BASE}/settings/`, {
    body: settings,
  });
  if (error || !data) {
    throw new Error(errorMessage(error, "Failed to update user settings"));
  }
  return data;
}

// -- Overviews

export async function fetchCharacterOverview(): Promise<CharacterOverview[]> {
  const { data, error } = await apiClient.GET(`${API_BASE}/character/overview/`);
  if (error || !data) {
    throw new Error(errorMessage(error, "Failed to load characters"));
  }
  return data;
}

export async function fetchPlanetaryOverview(): Promise<CharacterOverview[]> {
  const { data, error } = await apiClient.GET(`${API_BASE}/planetary/overview/`);
  if (error || !data) {
    throw new Error(errorMessage(error, "Failed to load characters"));
  }
  return data;
}

export async function fetchCorporationOverview(): Promise<CorporationOverview[]> {
  const { data, error } = await apiClient.GET(`${API_BASE}/corporation/overview/`);
  if (error || !data) {
    throw new Error(errorMessage(error, "Failed to load corporations"));
  }
  return data;
}

export async function fetchAllianceOverview(): Promise<AllianceOverview[]> {
  const { data, error } = await apiClient.GET(`${API_BASE}/alliance/overview/`);
  if (error || !data) {
    throw new Error(errorMessage(error, "Failed to load alliances"));
  }
  return data;
}

// -- Ledgers

export async function fetchCharacterLedger(
  characterId: number,
  filters: DateFilterParams,
): Promise<CharacterLedgerResponse> {
  const { data, error } = await apiClient.GET(`${API_BASE}/character/{character_id}/ledger/`, {
    params: { path: { character_id: characterId }, query: filters },
  });
  if (error || !data) {
    throw new Error(errorMessage(error, "Failed to load the character ledger"));
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
    throw new Error(errorMessage(error, "Failed to load the corporation ledger"));
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
    throw new Error(errorMessage(error, "Failed to load the alliance ledger"));
  }
  return data;
}

// -- Ledger details

export async function fetchCharacterDetails(
  characterId: number,
  filters: DateFilterParams,
  section: Section,
): Promise<LedgerDetailsResponse> {
  const { data, error } = await apiClient.GET(`${API_BASE}/character/{character_id}/details/`, {
    params: { path: { character_id: characterId }, query: { ...filters, section } },
  });
  if (error || !data) {
    throw new Error(errorMessage(error, "Failed to load the details"));
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
    throw new Error(errorMessage(error, "Failed to load the details"));
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
    throw new Error(errorMessage(error, "Failed to load the details"));
  }
  return data;
}

// -- Planetary

export async function fetchPlanets(
  characterId: number,
): Promise<PlanetaryDetails[]> {
  const { data, error } = await apiClient.GET(`${API_BASE}/character/{character_id}/planets/`, {
    params: { path: { character_id: characterId } },
  });
  if (error || !data) {
    throw new Error(errorMessage(error, "Failed to load the planets"));
  }
  return data;
}

export async function fetchPlanetDetails(
  characterId: number,
  planetId: number,
): Promise<PlanetDetailResponse> {
  const { data, error } = await apiClient.GET(
    `${API_BASE}/character/{character_id}/planets/{planet_id}/`,
    { params: { path: { character_id: characterId, planet_id: planetId } } },
  );
  if (error || !data) {
    throw new Error(errorMessage(error, "Failed to load the planet"));
  }
  return data;
}

/** Toggles the expiry notification of one planet, or of all planets if `planetId` is omitted. */
export async function togglePlanetNotification(
  characterId: number,
  planetId?: number,
): Promise<NotificationResponse> {
  const { data, error } = await apiClient.POST(
    `${API_BASE}/character/{character_id}/planets/notification/`,
    {
      params: {
        path: { character_id: characterId },
        query: planetId === undefined ? {} : { planet_id: planetId },
      },
    },
  );
  if (error || !data) {
    throw new Error(errorMessage(error, "Failed to toggle the notification"));
  }
  return data;
}

// -- Administration

export async function fetchCharacterAdministration(
  characterId: number,
): Promise<AdministrationResponse> {
  const { data, error } = await apiClient.GET(
    `${API_BASE}/character/{character_id}/administration/`,
    { params: { path: { character_id: characterId } } },
  );
  if (error || !data) {
    throw new Error(errorMessage(error, "Failed to load the administration"));
  }
  return data;
}

export async function fetchCorporationAdministration(
  corporationId: number,
): Promise<AdministrationResponse> {
  const { data, error } = await apiClient.GET(
    `${API_BASE}/corporation/{corporation_id}/administration/`,
    { params: { path: { corporation_id: corporationId } } },
  );
  if (error || !data) {
    throw new Error(errorMessage(error, "Failed to load the administration"));
  }
  return data;
}

export async function fetchAllianceAdministration(
  allianceId: number,
): Promise<AdministrationResponse> {
  const { data, error } = await apiClient.GET(
    `${API_BASE}/alliance/{alliance_id}/administration/`,
    { params: { path: { alliance_id: allianceId } } },
  );
  if (error || !data) {
    throw new Error(errorMessage(error, "Failed to load the administration"));
  }
  return data;
}

export async function deleteCharacter(characterId: number): Promise<MessageSchema> {
  const { data, error } = await apiClient.DELETE(`${API_BASE}/character/{character_id}/`, {
    params: { path: { character_id: characterId } },
  });
  if (error || !data) {
    throw new Error(errorMessage(error, "Failed to delete the character"));
  }
  return data;
}

export async function deleteCorporation(corporationId: number): Promise<MessageSchema> {
  const { data, error } = await apiClient.DELETE(`${API_BASE}/corporation/{corporation_id}/`, {
    params: { path: { corporation_id: corporationId } },
  });
  if (error || !data) {
    throw new Error(errorMessage(error, "Failed to delete the corporation"));
  }
  return data;
}

export async function queueUpdate(request: AdminUpdateRequest): Promise<MessageSchema> {
  const { data, error } = await apiClient.POST(`${API_BASE}/admin/update/`, {
    body: request,
  });
  if (error || !data) {
    throw new Error(errorMessage(error, "Failed to queue the update"));
  }
  return data;
}
