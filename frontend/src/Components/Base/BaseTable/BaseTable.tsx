// React
import { useLocation } from "react-router";

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
  Cell,
  ColumnDef,
  InitialTableState,
  Row,
} from "@tanstack/react-table";
import {
  ArrowUpDown,
  ChevronDown,
  ChevronFirst,
  ChevronLast,
  ChevronLeft,
  ChevronRight,
  ChevronUp,
} from "lucide-react";
import { Button, Form, Table } from "react-bootstrap";
import { useTranslation } from "react-i18next";

// Styles
import styles from "@/Styles/modules/BaseTable.module.css";

import BaseHeader from "@/Components/Base/BaseTable/BaseTableHeader";
import BasePages from "@/Components/Base/BaseTable/BaseTablePages";

const isNumber = <TData,>(cell: Cell<TData, unknown>) => typeof cell.getValue() === "number";

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
  variant?: "bootstrap" | "vowra";
  emptyText?: string;
  className?: string;
  tableClassName?: string;
  pageSizeOptions?: number[];
  itemLabel?: string;
  getRowClassName?: (row: Row<TData>) => string;
}

const BaseTable = <TData, TValue = unknown>({
  isFetching = false,
  isError = false,
  debugTable = false,
  data = [],
  columns,
  striped = false,
  hover = false,
  initialState = undefined,
  exportFileName = undefined,
  variant = "vowra",
  emptyText,
  className,
  tableClassName,
  pageSizeOptions = [10, 25, 50, 100],
  itemLabel,
  getRowClassName,
}: BaseTableProps<TData, TValue>) => {
  const location = useLocation();
  const { t } = useTranslation();

  // TanStack Table's useReactTable() returns functions the compiler can't
  // safely memoize; this is inherent to the library, not fixable here.
  // eslint-disable-next-line react-hooks/incompatible-library
  const table = useReactTable({
    data,
    columns,
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

  if (variant === "vowra") {
    const totalCount = table.getPrePaginationRowModel().rows.length;
    const pageIndex = table.getState().pagination.pageIndex;
    const pageSize = table.getState().pagination.pageSize;
    const pageCount = table.getPageCount();

    return (
      <div
        className={`aa-table-shell ${className ?? ""}`}
      >
        <div className="aa-table-scroll">
          <table
            className={`aa-table ${tableClassName ?? ""}`}
          >
            <thead className="aa-table-head">
              {table.getHeaderGroups().map((headerGroup) => (
                <tr key={headerGroup.id}>
                  {headerGroup.headers.map((header) => {
                    const canSort = header.column.getCanSort();
                    const isSorted = header.column.getIsSorted();
                    const meta = header.column.columnDef.meta as { align?: string } | undefined;
                    const isRight = meta?.align === "right";
                    return (
                      <th
                        key={header.id}
                        colSpan={header.colSpan}
                        onClick={canSort ? header.column.getToggleSortingHandler() : undefined}
                        className={`aa-table-heading-cell ${
                          canSort
                            ? "aa-table-sortable"
                            : ""
                        } ${isRight ? "text-end aa-table-cell-right" : ""}`}
                      >
                        <div
                          className={`aa-table-heading ${
                            isRight ? "aa-table-heading-right justify-content-end" : ""
                          }`}
                        >
                          {flexRender(header.column.columnDef.header, header.getContext())}
                          {canSort && (
                            <span>
                              {isSorted === "asc" ? (
                                <ChevronUp className="aa-table-sort-icon aa-table-sort-icon-active" />
                              ) : isSorted === "desc" ? (
                                <ChevronDown className="aa-table-sort-icon aa-table-sort-icon-active" />
                              ) : (
                                <ArrowUpDown className="aa-table-sort-icon" />
                              )}
                            </span>
                          )}
                        </div>
                      </th>
                    );
                  })}
                </tr>
              ))}
            </thead>
            <tbody className="aa-table-body">
              {isError ? (
                <tr>
                  <td
                    colSpan={table.getVisibleLeafColumns().length}
                    className="aa-table-message"
                  >
                    {t("Something went wrong.")}
                  </td>
                </tr>
              ) : rows.length === 0 ? (
                <tr>
                  <td
                    colSpan={table.getVisibleLeafColumns().length}
                    className="aa-table-message"
                  >
                    {emptyText ?? t("No Data Available")}
                  </td>
                </tr>
              ) : (
                rows.map((row) => (
                  <tr
                    key={row.id}
                    className={`aa-table-row ${
                      getRowClassName
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
                          className={`aa-table-cell ${styles["cell-middle"]} ${
                            isRight ? styles["cell-right"] : ""
                          }`}
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
        <div className="aa-table-footer">
          {/* Page Size Selector & Count Indicator */}
          <div className="aa-table-controls">
            <div className="aa-table-page-size">
              <span>{t("Page Size:")}</span>
              <Form.Select
                size="sm"
                value={pageSize}
                onChange={(e) => table.setPageSize(Number(e.target.value))}
                className={`aa-table-select ${styles["page-size-select"]}`}
              >
                {pageSizeOptions.map((size) => (
                  <option key={size} value={size}>
                    {size}
                  </option>
                ))}
                <option value={1000000}>{t("Show All")}</option>
              </Form.Select>
            </div>

            {totalCount > 0 && (
              <span className="aa-table-count">
                {pageSize >= 1000000
                  ? t("Showing all {{total}} {{items}}", {
                      total: totalCount,
                      items: itemLabel ?? t("entries"),
                    })
                  : t("Showing {{start}}-{{end}} of {{total}} {{items}}", {
                      start: pageIndex * pageSize + 1,
                      end: Math.min((pageIndex + 1) * pageSize, totalCount),
                      total: totalCount,
                      items: itemLabel ?? t("entries"),
                    })}
              </span>
            )}
          </div>

          {/* Pagination Buttons */}
          {pageCount > 1 && (
            <div className="aa-table-pagination">
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

              <span className="aa-table-page-number">
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
      </div>
    );
  }

  return (
    <>
      <Table {...{ striped, hover }}>
        <thead>
          <BaseHeader table={table} />
        </thead>
        <tbody>
          {isError ? (
            <tr>
              <td className="text-center" colSpan={table.getVisibleLeafColumns().length}>
                {t("No Data Available")}
              </td>
            </tr>
          ) : (
            rows.map((row) => (
              <tr key={row.id}>
                {row.getVisibleCells().map((cell) => (
                  <td
                    key={cell.id}
                    className={`${styles["cell-middle"]} ${isNumber(cell) ? styles["cell-right"] : styles["cell-left"]}`}
                  >
                    {flexRender(cell.column.columnDef.cell, cell.getContext())}
                  </td>
                ))}
              </tr>
            ))
          )}
        </tbody>
      </Table>
      <BasePages table={table} isFetching={isFetching} fileName={fileName} />
      {debugTable && (
        <div className="col-xs-12">
          <div>{t("{{count}} Rows", { count: table.getRowModel().rows.length })}</div>
          <pre>{JSON.stringify(table.getState(), null, 2)}</pre>
        </div>
      )}
    </>
  );
};

export default BaseTable;
