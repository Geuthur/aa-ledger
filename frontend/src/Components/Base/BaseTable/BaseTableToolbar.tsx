// Third Party
import type { Table as TanStackTable } from "@tanstack/react-table";
import { Button, ButtonGroup, ButtonToolbar } from "react-bootstrap";

// Styles
import pageStyles from "@/Styles/modules/BaseTablePages.module.css";

import { BaseTableForm } from "@/Components/Base/BaseTable/BaseTableForm";

export interface TableToolbarProps<TData> {
  table: TanStackTable<TData>;
}

export const BaseToolbar = <TData,>({ table }: TableToolbarProps<TData>) => {
  return (
    <ButtonToolbar>
      <ButtonGroup className={pageStyles["button-group"]}>
        <Button
          variant="success"
          onClick={() => table.setPageIndex(0)}
          disabled={!table.getCanPreviousPage()}
        >
          <i className="fas fa-angle-double-left"></i>
        </Button>
        <Button
          variant="success"
          onClick={() => table.previousPage()}
          disabled={!table.getCanPreviousPage()}
        >
          <i className="fas fa-caret-left"></i>
        </Button>
        <Button
          variant="success"
          onClick={() => table.nextPage()}
          disabled={!table.getCanNextPage()}
        >
          <i className="fas fa-caret-right"></i>
        </Button>
        <Button
          variant="success"
          onClick={() => table.setPageIndex(table.getPageCount() - 1)}
          disabled={!table.getCanNextPage()}
        >
          <i className="fas fa-angle-double-right"></i>
        </Button>
      </ButtonGroup>

      <BaseTableForm table={table} />
    </ButtonToolbar>
  );
};