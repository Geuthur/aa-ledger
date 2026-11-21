// Third Party
import { apiErrorMessage } from "aa-geuthur-react";

// AA Ledger
import { apiClient } from "@/Api/Api";
import type {
  NotificationResponse,
  PlanetaryDetails,
  PlanetDetailResponse,
} from "@/Api/schema";

// Literal on purpose: App.tsx imports the pages, so importing ProjectName here would be circular.
const API_BASE = "/ledger/api";

/** Query keys of the planetary area: the planets of a character and one planet. */
export const planetaryQueryKeys = {
  planets: (characterId: number) => ["Planets", characterId] as const,
  planet: (characterId: number, planetId: number) =>
    ["PlanetDetails", characterId, planetId] as const,
};

export async function fetchPlanets(
  characterId: number,
): Promise<PlanetaryDetails[]> {
  const { data, error } = await apiClient.GET(`${API_BASE}/character/{character_id}/planets/`, {
    params: { path: { character_id: characterId } },
  });
  if (error || !data) {
    throw new Error(apiErrorMessage(error, "Failed to load the planets"));
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
    throw new Error(apiErrorMessage(error, "Failed to load the planet"));
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
    throw new Error(apiErrorMessage(error, "Failed to toggle the notification"));
  }
  return data;
}
