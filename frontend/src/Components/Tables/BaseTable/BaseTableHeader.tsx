
// React
import { Fragment } from "react/jsx-runtime";

// Third Party
import { flexRender } from "@tanstack/react-table";
import type { Header, HeaderGroup, Table as TanStackTable } from "@tanstack/react-table";

import { Filter } from "@/Components/Tables/BaseTable/BaseTableFilter";

export interface TableHeaderProps<TData> {
  table: TanStackTable<TData>;
}

const BaseHeader = <TData,>({ table }: TableHeaderProps<TData>) => {
    return (
        <>
            {table.getHeaderGroups().map((headerGroup: HeaderGroup<TData>) => (
            <Fragment key={headerGroup.id}>
              <tr>
                {headerGroup.headers.map((header: Header<TData, unknown>) => (
                  <th key={header.id} colSpan={header.colSpan}>
                    {header.isPlaceholder ? null : (
                      <div
                        className={
                          header.column.getCanSort()
                            ? "d-flex align-items-center cursor-pointer select-none"
                            : "d-flex align-items-center"
                        }
                        onClick={header.column.getToggleSortingHandler()}
                      >
                        {header.column.getCanSort() && (
                          <div>
                            {{
                              asc: <i className="fas fa-sort-down fa-fw"></i>,
                              desc: <i className="fas fa-sort-up fa-fw"></i>,
                            }[header.column.getIsSorted() as string] ?? (
                              <i className="fas fa-sort fa-fw"></i>
                            )}
                          </div>
                        )}
                        {flexRender(header.column.columnDef.header, header.getContext())}
                      </div>
                    )}
                  </th>
                ))}
              </tr>
              <tr>
                {headerGroup.headers.map((header) => (
                  <th key={header.id} colSpan={header.colSpan}>
                    {header.column.getCanFilter() ? (
                      <Filter column={header.column} table={table} />
                    ) : null}
                  </th>
                ))}
              </tr>
            </Fragment>
          ))}
        </>
    );
};

export default BaseHeader;
