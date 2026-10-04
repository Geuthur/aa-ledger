// Third Party
import type { Table as TanStackTable } from "@tanstack/react-table";
import {
  Button,
  ButtonGroup,
  ButtonToolbar,
} from "react-bootstrap";
import { useTranslation } from "react-i18next";

// Styles
import tableStyles from "@/Components/Tables/BaseTable/BaseTable.module.css";
import pageStyles from "@/Components/Tables/BaseTable/BaseTablePages.module.css";

import { BaseTableForm } from "@/Components/Tables/BaseTable/BaseTableForm";
import { exportToCSV, renderTooltip } from "@/Components/Tables/BaseTable/tableHelper";

export interface TablePagesProps<TData> {
  table: TanStackTable<TData>;
  isFetching?: boolean;
  fileName?: string;
}

const BasePages = <TData,>({
  table,
  isFetching = false,
  fileName,
}: TablePagesProps<TData>) => {
  const { t } = useTranslation();
  const pageCount = Math.max(1, table.getPageCount());

  return (
    <div className="d-flex justify-content-between">
      <ButtonGroup className={pageStyles["button-group"]}>
        <Button active variant="info">
          {t("Page {{page}} of {{total}}", {
            page: table.getState().pagination.pageIndex + 1,
            total: pageCount,
          })}
        </Button>
        {isFetching ? (
          renderTooltip(
            t("Refreshing Data"),
            <Button variant="info">
              <i className={`${tableStyles.refreshanimate} fas fa-sync`}></i>
            </Button>
          )
        ) : (
          renderTooltip(
            t("Data Loaded: {{date}}", { date: new Date().toLocaleString() }),
            <Button variant="info">
              <i className="far fa-check-circle"></i>
            </Button>
          )
        )}
        <Button
          variant="primary"
          onClick={() => exportToCSV(table, fileName ?? "ExportedData.csv")}
        >
          {t("Export Table to CSV")}
        </Button>
      </ButtonGroup>

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
    </div>
  );
};

export default BasePages;
