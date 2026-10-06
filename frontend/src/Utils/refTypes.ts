import type { CategorySchema, CharacterRefTypeSchema, RefTypeAmountSchema } from "@/Api/schema";

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
  const totals = new Map<string, { amount: number; characters: Map<number, CharacterRefTypeSchema> }>();
  for (const row of rows) {
    for (const item of filterRefTypes(row.ref_types ?? [], term)) {
      const existing = totals.get(item.ref_type);
      const amount = (existing?.amount ?? 0) + (item.amount ?? 0);
      const charMap = existing?.characters ?? new Map<number, CharacterRefTypeSchema>();
      for (const char of item.characters ?? []) {
        const prev = charMap.get(char.character_id);
        if (prev) {
          prev.amount += char.amount;
        } else {
          charMap.set(char.character_id, { ...char });
        }
      }
      totals.set(item.ref_type, { amount, characters: charMap });
    }
  }
  return [...totals.entries()]
    .map(([ref_type, { amount, characters }]) => ({
      ref_type,
      amount,
      characters: [...characters.values()].sort((a, b) => Math.abs(b.amount) - Math.abs(a.amount)),
    }))
    .sort((a, b) => Math.abs(b.amount) - Math.abs(a.amount));
}
