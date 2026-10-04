import type {
  AllianceLedgerResponse,
  AltSchema,
  CharacterLedgerResponse,
  CorporationLedgerResponse,
  LedgerSchema,
} from "@/Api/schema";
import { formatNumber } from "@/Components/Tables/BaseTable/tableHelper";

/** A row of the ledger table, independent of the owner type. */
export interface LedgerRow {
  id: number;
  name: string;
  icon?: string | null;
  alts: AltSchema[];
  bounty: number;
  ess: number;
  /** Only characters mine; shown for information and not part of `total`. */
  mining?: number;
  miscellaneous: number;
  costs: number;
  total: number;
  status?: string | null;
}

export type LedgerTotals = Pick<
  LedgerRow,
  "bounty" | "ess" | "mining" | "miscellaneous" | "costs" | "total"
>;

const amounts = (ledger: LedgerSchema) => ({
  bounty: ledger.bounty ?? 0,
  ess: ledger.ess ?? 0,
  miscellaneous: ledger.miscellaneous ?? 0,
  costs: ledger.costs ?? 0,
  total: ledger.total ?? 0,
});

export function characterRows(response?: CharacterLedgerResponse): LedgerRow[] {
  return (response?.characters ?? []).map(({ character, ledger, update_status }) => ({
    id: character.character_id,
    name: character.character_name,
    icon: character.icon,
    alts: [],
    ...amounts(ledger),
    mining: ledger.mining ?? 0,
    status: update_status.status,
  }));
}

export function entityRows(response?: CorporationLedgerResponse): LedgerRow[] {
  return (response?.entities ?? []).map(({ entity, ledger }) => ({
    id: entity.entity_id,
    name: entity.entity_name,
    icon: entity.icon,
    alts: entity.alts ?? [],
    ...amounts(ledger),
  }));
}

export function corporationRows(response?: AllianceLedgerResponse): LedgerRow[] {
  return (response?.corporations ?? []).map(({ corporation, ledger, update_status }) => ({
    id: corporation.entity_id,
    name: corporation.entity_name,
    icon: corporation.icon,
    alts: [],
    ...amounts(ledger),
    status: update_status?.status,
  }));
}

export function sumRows(rows: LedgerRow[]): LedgerTotals {
  const totals: LedgerTotals = { bounty: 0, ess: 0, mining: 0, miscellaneous: 0, costs: 0, total: 0 };
  for (const row of rows) {
    totals.bounty += row.bounty;
    totals.ess += row.ess;
    totals.mining = (totals.mining ?? 0) + (row.mining ?? 0);
    totals.miscellaneous += row.miscellaneous;
    totals.costs += row.costs;
    totals.total += row.total;
  }
  return totals;
}

/** Bootstrap text colour of an amount; mining is informational and therefore never red. */
export function amountClass(value: number, mining = false): string {
  if (value === 0) return "";
  if (mining) return "text-info";
  return value > 0 ? "text-success" : "text-danger";
}

export function formatIsk(value: number): string {
  return `${formatNumber(Math.round(value), undefined, { maximumFractionDigits: 0 })} ISK`;
}
