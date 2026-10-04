import type { CategorySchema, RefTypeAmountSchema } from "@/Api/schema";

/** Number of reference types shown as badges before the rest moves into a modal. */
export const MAX_REF_TYPE_BADGES = 10;

/** `market_transaction` -> `Market Transaction` */
export const formatRefType = (refType: string): string =>
  refType.replace(/_/g, " ").replace(/\b\w/g, (letter) => letter.toUpperCase());

/** Reference types that contain the search term; spaces and underscores are equivalent. */
export function filterRefTypes(refTypes: RefTypeAmountSchema[], term: string): RefTypeAmountSchema[] {
  const needle = term.trim().toLowerCase().replace(/\s+/g, "_");
  return needle ? refTypes.filter((item) => item.ref_type.toLowerCase().includes(needle)) : refTypes;
}

/** Categories that have a matching reference type; all of them without a search term. */
export function filterCategories(rows: CategorySchema[], term: string): CategorySchema[] {
  return term.trim()
    ? rows.filter((row) => filterRefTypes(row.ref_types ?? [], term).length > 0)
    : rows;
}

/** Amount per matching reference type across all categories, largest absolute amount first. */
export function sumRefTypes(rows: CategorySchema[], term: string): RefTypeAmountSchema[] {
  const totals = new Map<string, number>();
  for (const row of rows) {
    for (const item of filterRefTypes(row.ref_types ?? [], term)) {
      totals.set(item.ref_type, (totals.get(item.ref_type) ?? 0) + (item.amount ?? 0));
    }
  }
  return [...totals.entries()]
    .map(([ref_type, amount]) => ({ ref_type, amount }))
    .sort((a, b) => Math.abs(b.amount) - Math.abs(a.amount));
}
