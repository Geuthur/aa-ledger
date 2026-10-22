import type { components } from "@/Api/OpenApi";

export type MenuLink = components["schemas"]["MenuLink"];
export type MenuSchema = components["schemas"]["MenuSchema"];
export type UserData = components["schemas"]["UserData"];
export type UserSettingsSchema = components["schemas"]["UserSettingsSchema"];
export type UserSettingsUpdateRequest = components["schemas"]["UserSettingsUpdateRequest"];
export type AdminUpdateRequest = components["schemas"]["AdminUpdateRequest"];
export type MessageSchema = components["schemas"]["MessageSchema"];

export type CharacterOverview = components["schemas"]["CharacterOverview"];
export type CorporationOverview = components["schemas"]["CorporationOverview"];
export type AllianceOverview = components["schemas"]["AllianceOverview"];
export type LedgerOverviewOwnerSchema = components["schemas"]["LedgerOverviewOwnerSchema"];
export type LedgerOverviewResponse = components["schemas"]["LedgerOverviewResponse"];
export type DashboardSchema = components["schemas"]["DashboardSchema"];
export type AdministrationResponse = components["schemas"]["AdministrationResponse"];
export type AdminOwnerSchema = components["schemas"]["AdminOwnerSchema"];
export type AdminOwnerSectionSchema = components["schemas"]["AdminOwnerSectionSchema"];
export type SuperuserOwnerSchema = components["schemas"]["SuperuserOwnerSchema"];
export type SuperuserOwnerUpdateRequest = components["schemas"]["SuperuserOwnerUpdateRequest"];
export type SettingsOwnerSectionSchema = components["schemas"]["SettingsOwnerSectionSchema"];
export type SettingsOwnerSchema = components["schemas"]["SettingsOwnerSchema"];
export type SettingsMissingOwnerSchema = components["schemas"]["SettingsMissingOwnerSchema"];
export type SettingsOwnersResponse = components["schemas"]["SettingsOwnersResponse"];
export type SettingsUnregisteredResponse = components["schemas"]["SettingsUnregisteredResponse"];

export type BillboardData = components["schemas"]["BillboardData"];
export type BillboardSchema = components["schemas"]["BillboardSchema"];
export type CharacterLedgerResponse = components["schemas"]["CharacterLedgerResponse"];
export type CorporationLedgerResponse = components["schemas"]["CorporationLedgerResponse"];
export type AllianceLedgerResponse = components["schemas"]["AllianceLedgerResponse"];
export type LedgerSchema = components["schemas"]["LedgerSchema"];
export type AltSchema = components["schemas"]["AltSchema"];
export type AltLedgerSchema = components["schemas"]["AltLedgerSchema"];
export type CharacterLedgerSchema = components["schemas"]["CharacterLedgerSchema"];
export type UpdateStatusSchema = components["schemas"]["UpdateStatusSchema"];
export type DivisionSchema = components["schemas"]["DivisionSchema"];
export type LedgerDetailsResponse = components["schemas"]["LedgerDetailsResponse"];
export type CategorySchema = components["schemas"]["CategorySchema"];
export type RefTypeAmountSchema = components["schemas"]["RefTypeAmountSchema"];
export type CharacterRefTypeSchema = components["schemas"]["CharacterRefTypeSchema"];

export type PlanetaryDetails = components["schemas"]["PlanetaryDetails"];
export type PlanetDetailResponse = components["schemas"]["PlanetDetailResponse"];
export type NotificationResponse = components["schemas"]["NotificationResponse"];

/** Date range shared by all ledger endpoints. */
export interface DateFilterParams {
  year: number;
  month?: number;
  day?: number;
}

export interface CorporationFilterParams extends DateFilterParams {
  division_id?: number;
}

export type Section = "single" | "summary";
