// React
import { useLocation } from "react-router-dom";

// Third Party
import {
  flexRender,
  getCoreRowModel,
  getFacetedMinMaxValues,
  getFacetedRowModel,
  getFacetedUniqueValues,
  getFilteredRowModel,
  getPaginationRowModel,
  getSortedRowModel,
  useReactTable,
} from "@tanstack/react-table";
import type {
  ColumnDef,
  InitialTableState,
  OnChangeFn,
  Row,
  RowSelectionState,
} from "@tanstack/react-table";
import {
  ChevronFirst,
  ChevronLast,
  ChevronLeft,
  ChevronRight,
} from "lucide-react";
import { Button, Form } from "react-bootstrap";
import { useTranslation } from "react-i18next";

import BaseHeader from "@/Components/Base/BaseTable/BaseTableHeader";
import BasePages from "@/Components/Base/BaseTable/BaseTablePages";

export interface BaseTableProps<TData, TValue = unknown> {
  isFetching?: boolean;
  isError?: boolean;
  debugTable?: boolean;
  striped?: boolean;
  hover?: boolean;
  data?: TData[];
  columns: ColumnDef<TData, TValue>[];
  initialState?: InitialTableState;
  exportFileName?: string;
  variant?: "default" | "light";
  emptyText?: string;
  className?: string;
  tableClassName?: string;
  pageSizeOptions?: number[];
  itemLabel?: string;
  getRowClassName?: (row: Row<TData>) => string;
  enableFilters?: boolean;
  rowSelection?: RowSelectionState;
  onRowSelectionChange?: OnChangeFn<RowSelectionState>;
  enableRowSelection?: boolean | ((row: Row<TData>) => boolean);
  getRowId?: (originalRow: TData, index: number, parent?: Row<TData>) => string;
  onRowClick?: (row: Row<TData>) => void;
}

const BaseTable = <TData, TValue = unknown>({
  isFetching = false,
  isError = false,
  debugTable = false,
  data = [],
  columns,
  initialState = undefined,
  exportFileName = undefined,
  variant = "default",
  emptyText,
  className,
  tableClassName,
  pageSizeOptions = [10, 25, 50, 100],
  getRowClassName,
  enableFilters = true,
  rowSelection,
  onRowSelectionChange,
  enableRowSelection,
  getRowId,
  onRowClick,
}: BaseTableProps<TData, TValue>) => {
  const location = useLocation();
  const { t } = useTranslation();

  // TanStack Table's useReactTable() returns functions the compiler can't
  // safely memoize; this is inherent to the library, not fixable here.
  // eslint-disable-next-line react-hooks/incompatible-library
  const table = useReactTable({
    data,
    columns,
    getRowId,
    state: {
      ...(rowSelection !== undefined ? { rowSelection } : {}),
    },
    onRowSelectionChange,
    enableRowSelection,
    getCoreRowModel: getCoreRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
    getFacetedRowModel: getFacetedRowModel(),
    getFacetedUniqueValues: getFacetedUniqueValues(),
    getFacetedMinMaxValues: getFacetedMinMaxValues(),
    debugTable,
    initialState: {
      pagination: { pageSize: 15 },
      ...initialState,
    },
  });

  const { rows } = table.getRowModel();
  const fileName =
    exportFileName !== undefined ? exportFileName : `ExportedData_${location.pathname}`;

  const isLight = variant === "light";
  const pageIndex = table.getState().pagination.pageIndex;
  const pageSize = table.getState().pagination.pageSize;
  const pageCount = table.getPageCount();

  return (
    <div
      className={`aa-table-shell mt-2 ${isLight ? "aa-table-shell-light aa-table-light" : ""} ${className ?? ""}`}
    >
      <div className="aa-table-scroll">
        <table
          className={`aa-table w-100 text-start ${isLight ? "aa-table-light" : ""} ${tableClassName ?? ""}`}
        >
          <thead className="aa-table-head">
            <BaseHeader table={table} enableFilters={enableFilters} />
          </thead>
          <tbody className="aa-table-body">
            {isError ? (
              <tr>
                <td
                  colSpan={table.getVisibleLeafColumns().length}
                  className="aa-table-message text-center py-5 px-3"
                >
                  {t("Something went wrong.")}
                </td>
              </tr>
            ) : rows.length === 0 ? (
              <tr>
                <td
                  colSpan={table.getVisibleLeafColumns().length}
                  className="aa-table-message text-center py-5 px-3"
                >
                  {emptyText ?? t("No Data Available")}
                </td>
              </tr>
            ) : (
              rows.map((row) => (
                <tr
                  key={row.id}
                  onClick={onRowClick ? () => onRowClick(row) : undefined}
                  className={`aa-table-row ${getRowClassName
                    ? getRowClassName(row)
                    : "aa-table-row-hover"
                    }`}
                >
                  {row.getVisibleCells().map((cell) => {
                    const meta = cell.column.columnDef.meta as { align?: string } | undefined;
                    const isRight = meta?.align === "right";
                    return (
                      <td
                        key={cell.id}
                        className={`aa-table-cell align-middle ${isRight ? "text-end" : ""}`}
                      >
                        {flexRender(cell.column.columnDef.cell, cell.getContext())}
                      </td>
                    );
                  })}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* DataTable Footer Controls */}
      <div className="aa-table-footer d-flex flex-column align-items-center justify-content-between gap-3 p-3">
        {/* Page Size Selector, Count Indicator & Export / Status */}
        <div className="d-flex w-100 align-items-center justify-content-between gap-3">
          <div className="d-flex align-items-center gap-3">
            <div className="d-flex align-items-center gap-2">
              <span>{t("Page Size:")}</span>
              <Form.Select
                size="sm"
                value={pageSize}
                onChange={(e) => table.setPageSize(Number(e.target.value))}
                className="aa-table-select w-auto"
              >
                {pageSizeOptions.map((size) => (
                  <option key={size} value={size}>
                    {size}
                  </option>
                ))}
                <option value={1000000}>{t("Show All")}</option>
              </Form.Select>
            </div>
          </div>

          <BasePages table={table} isFetching={isFetching} fileName={fileName} showPageNumber={true} />
        </div>
        {/* Pagination Buttons */}
        {pageCount > 1 && (
          <div className="d-flex align-items-center gap-2">
            <Button
              size="sm"
              disabled={!table.getCanPreviousPage()}
              onClick={() => table.setPageIndex(0)}
              className="aa-table-page-button"
              title={t("First Page")}
            >
              <ChevronFirst className="aa-table-page-icon" />
            </Button>
            <Button
              size="sm"
              disabled={!table.getCanPreviousPage()}
              onClick={() => table.previousPage()}
              className="aa-table-page-button"
              title={t("Previous Page")}
            >
              <ChevronLeft className="aa-table-page-icon" />
            </Button>

            <span className="aa-table-page-number px-2 fw-bold">
              {t("Page {{page}} of {{total}}", {
                page: pageIndex + 1,
                total: pageCount,
              })}
            </span>

            <Button
              size="sm"
              disabled={!table.getCanNextPage()}
              onClick={() => table.nextPage()}
              className="aa-table-page-button"
              title={t("Next Page")}
            >
              <ChevronRight className="aa-table-page-icon" />
            </Button>
            <Button
              size="sm"
              disabled={!table.getCanNextPage()}
              onClick={() => table.setPageIndex(pageCount - 1)}
              className="aa-table-page-button"
              title={t("Last Page")}
            >
              <ChevronLast className="aa-table-page-icon" />
            </Button>
          </div>
        )}
      </div>

      {debugTable && (
        <div className="p-3">
          <div>{t("{{count}} Rows", { count: table.getRowModel().rows.length })}</div>
          <pre>{JSON.stringify(table.getState(), null, 2)}</pre>
        </div>
      )}
    </div>
  );
};

export default BaseTable;
