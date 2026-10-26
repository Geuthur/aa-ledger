
// React
import { Fragment } from "react/jsx-runtime";

// Third Party
import { flexRender } from "@tanstack/react-table";
import type { Header, HeaderGroup, Table as TanStackTable } from "@tanstack/react-table";
import { ArrowUpDown, ChevronDown, ChevronUp } from "lucide-react";

import { Filter } from "@/Components/Base/BaseTable/BaseTableFilter";

export interface TableHeaderProps<TData> {
  table: TanStackTable<TData>;
  enableFilters?: boolean;
}

function BaseHeader<TData>({ table, enableFilters = true }: TableHeaderProps<TData>) {
  return (
    <>
      {table.getHeaderGroups().map((headerGroup: HeaderGroup<TData>) => {
        const hasFilters =
          enableFilters !== false &&
          headerGroup.headers.some((header) => header.column.getCanFilter());

        return (
          <Fragment key={headerGroup.id}>
            <tr>
              {headerGroup.headers.map((header: Header<TData, unknown>) => {
                const canSort = header.column.getCanSort();
                const isSorted = header.column.getIsSorted();
                const meta = header.column.columnDef.meta as { align?: string } | undefined;
                const isRight = meta?.align === "right";

                return (
                  <th
                    key={header.id}
                    colSpan={header.colSpan}
                    onClick={canSort ? header.column.getToggleSortingHandler() : undefined}
                    className={`aa-table-heading-cell ${canSort ? "aa-table-sortable user-select-none" : ""} ${
                      isRight ? "text-end" : ""
                    }`}
                  >
                    {header.isPlaceholder ? null : (
                      <div
                        className={`d-flex align-items-center gap-2 ${
                          isRight ? "justify-content-end text-end" : ""
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
                    )}
                  </th>
                );
              })}
            </tr>
            {hasFilters && (
              <tr className="aa-table-filter-row">
                {headerGroup.headers.map((header) => (
                  <th
                    key={`${header.id}-filter`}
                    colSpan={header.colSpan}
                    className="aa-table-filter-cell px-3 py-1"
                  >
                    {header.column.getCanFilter() ? (
                      <Filter column={header.column} table={table} />
                    ) : null}
                  </th>
                ))}
              </tr>
            )}
          </Fragment>
        );
      })}
    </>
  );
}

export default BaseHeader;
