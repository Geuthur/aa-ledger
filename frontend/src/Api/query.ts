// Third Party
import { queryKeys as baseQueryKeys } from "aa-geuthur-react";

// AA Ledger
import type { CorporationFilterParams, DateFilterParams, Section } from "@/Api/schema";

// Every key that influences a request is part of the key, so URL state changes refetch.
// `Menu`, `User` and `UserSettings` come from the package, so its hooks and the app share them.
export const queryKeys = {
  ...baseQueryKeys,
  SettingsOwners: ["SettingsOwners"] as const,
  SettingsUnregistered: (ownerType: string, ownerId: number) =>
    ["SettingsUnregistered", ownerType, ownerId] as const,
  Overview: ["Overview"] as const,

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


  AdministrationOwners: ["AdministrationOwners"] as const,
  AdministrationOwnerInspect: (ownerType: string, ownerId: number) =>
    ["AdministrationOwnerInspect", ownerType, ownerId] as const,
};
