// Third Party
import {
  columnFacetingFeature,
  columnFilteringFeature,
  columnSizingFeature,
  columnVisibilityFeature,
  createColumnHelper,
  createFacetedMinMaxValues,
  createFacetedRowModel,
  createFacetedUniqueValues,
  createFilteredRowModel,
  createPaginatedRowModel,
  createSortedRowModel,
  filterFns,
  rowPaginationFeature,
  rowSelectionFeature,
  rowSortingFeature,
  sortFns,
  tableFeatures,
} from "@tanstack/react-table";
import type { ColumnDef, RowData } from "@tanstack/react-table";

// TanStack Table v9 only exposes the APIs of registered features. BaseTable
// uses filtering (with faceted values for the filter widgets), sorting,
// pagination, row selection, visibility and column sizing (the `size` hint of
// some column definitions), so every table shares this set.
export const baseTableFeatures = tableFeatures({
  columnFilteringFeature,
  columnFacetingFeature,
  columnSizingFeature,
  columnVisibilityFeature,
  rowSortingFeature,
  rowPaginationFeature,
  rowSelectionFeature,
  filteredRowModel: createFilteredRowModel(),
  sortedRowModel: createSortedRowModel(),
  paginatedRowModel: createPaginatedRowModel(),
  facetedRowModel: createFacetedRowModel(),
  facetedUniqueValues: createFacetedUniqueValues(),
  facetedMinMaxValues: createFacetedMinMaxValues(),
  filterFns,
  sortFns,
});

export type BaseTableFeatures = typeof baseTableFeatures;

// eslint-disable-next-line @typescript-eslint/no-explicit-any -- columns of one table have different value types
export type BaseColumnDef<TData extends RowData, TValue = any> = ColumnDef<BaseTableFeatures, TData, TValue>;

export const createBaseColumnHelper = <TData extends RowData>() =>
  createColumnHelper<BaseTableFeatures, TData>();
