import type { CorporationFilterParams, DateFilterParams, Section } from "@/Api/schema";

// Every key that influences a request is part of the key, so URL state changes refetch.
export const queryKeys = {
  Menu: ["Menu"] as const,
  User: ["User"] as const,
  UserSettings: ["UserSettings"] as const,

  CharacterOverview: ["CharacterOverview"] as const,
  PlanetaryOverview: ["PlanetaryOverview"] as const,
  CorporationOverview: ["CorporationOverview"] as const,
  AllianceOverview: ["AllianceOverview"] as const,

  CharacterLedger: (characterId: number, filters: DateFilterParams) =>
    ["CharacterLedger", characterId, filters] as const,
  CorporationLedger: (corporationId: number, filters: CorporationFilterParams) =>
    ["CorporationLedger", corporationId, filters] as const,
  AllianceLedger: (allianceId: number, filters: DateFilterParams) =>
    ["AllianceLedger", allianceId, filters] as const,

  CharacterDetails: (characterId: number, filters: DateFilterParams, section: Section) =>
    ["CharacterDetails", characterId, filters, section] as const,
  CorporationDetails: (
    corporationId: number,
    entityId: number,
    filters: CorporationFilterParams,
    section: Section,
  ) => ["CorporationDetails", corporationId, entityId, filters, section] as const,
  AllianceDetails: (
    allianceId: number,
    entityId: number,
    filters: DateFilterParams,
    section: Section,
  ) => ["AllianceDetails", allianceId, entityId, filters, section] as const,

  Planets: (characterId: number) => ["Planets", characterId] as const,
  PlanetDetails: (characterId: number, planetId: number) =>
    ["PlanetDetails", characterId, planetId] as const,

  CharacterAdministration: (characterId: number) =>
    ["CharacterAdministration", characterId] as const,
  CorporationAdministration: (corporationId: number) =>
    ["CorporationAdministration", corporationId] as const,
  AllianceAdministration: (allianceId: number) =>
    ["AllianceAdministration", allianceId] as const,
};
