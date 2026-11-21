// Third Party
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

// AA Ledger
import {
  fetchPlanetDetails,
  fetchPlanets,
  planetaryQueryKeys,
  togglePlanetNotification,
} from "@/Api/calls/planetary";

/** Loads the planets of a character and its alts. */
export function usePlanets(characterId: number) {
  return useQuery({
    queryKey: planetaryQueryKeys.planets(characterId),
    queryFn: () => fetchPlanets(characterId),
  });
}

/** Loads the details of one planet; stays disabled until owner and planet are set. */
export function usePlanetDetails(ownerId: number | null, planetId: number | null) {
  return useQuery({
    queryKey: planetaryQueryKeys.planet(ownerId ?? 0, planetId ?? 0),
    queryFn: () => fetchPlanetDetails(ownerId ?? 0, planetId ?? 0),
    enabled: ownerId !== null && planetId !== null,
  });
}

/**
 * Toggles the planet notification of an owner (all planets when no planet is given)
 * and refreshes the planet list of the character.
 */
export function useTogglePlanetNotification(characterId: number) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ ownerId, planetId }: { ownerId: number; planetId?: number }) =>
      togglePlanetNotification(ownerId, planetId),
    onSuccess: () =>
      queryClient.invalidateQueries({ queryKey: planetaryQueryKeys.planets(characterId) }),
  });
}
