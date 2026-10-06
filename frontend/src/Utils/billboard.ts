import type { BillboardData } from "@/Api/schema";

export interface ChartSeries {
  name: string;
  data: number[];
}

export interface ChartModel {
  categories: string[];
  series: ChartSeries[];
}

const asNumber = (value: unknown): number => (typeof value === "number" ? value : 0);

/**
 * Time based chart: one stacked column per date, one series per ledger category.
 * Rows look like `{date: "2026-10", Bounty: 100, ESS: 50}`.
 */
export function buildTimelineChart(billboard?: BillboardData | null): ChartModel {
  if (!billboard) return { categories: [], series: [] };

  const categories = billboard.series.map((row) => String(row.date ?? ""));
  const series = billboard.categories.map((category) => ({
    name: String(category.label ?? category.name),
    data: billboard.series.map((row) => asNumber(row[String(category.name)])),
  }));
  return { categories, series };
}

/**
 * Chord diagram input: a square matrix where `matrix[from][to]` is the flow value.
 * Rows look like `{from: "Pilot", to: "Bounty", value: 100}`; sources come first, then targets.
 */
export function buildChordMatrix(billboard?: BillboardData | null): {
  names: string[];
  matrix: number[][];
} {
  if (!billboard) return { names: [], matrix: [] };

  const names = [
    ...new Set([
      ...billboard.series.map((row) => String(row.from)),
      ...billboard.series.map((row) => String(row.to)),
    ]),
  ];
  const matrix = names.map(() => names.map(() => 0));
  for (const row of billboard.series) {
    matrix[names.indexOf(String(row.from))][names.indexOf(String(row.to))] += asNumber(row.value);
  }
  return { names, matrix };
}
