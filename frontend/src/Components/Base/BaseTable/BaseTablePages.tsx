// Third Party
import type { RowData, Table as TanStackTable } from "@tanstack/react-table";
import {
  Button,
  ButtonGroup,
} from "react-bootstrap";
import { useTranslation } from "react-i18next";

// Styles
import tableStyles from "@/Styles/modules/BaseTable.module.css";
import pageStyles from "@/Styles/modules/BaseTablePages.module.css";

import type { BaseTableFeatures } from "@/Components/Base/BaseTable/tableFeatures";
import { exportToCSV } from "@/Components/Base/BaseTable/tableHelper";
import { renderTooltip } from "@/Utils/bootsTrap";
import { formatDate } from "@/Utils/format";

export interface TablePagesProps<TData extends RowData> {
  table: TanStackTable<BaseTableFeatures, TData>;
  isFetching?: boolean;
  fileName?: string;
  showPageNumber?: boolean;
  showExport?: boolean;
}

const BasePages = <TData extends RowData,>({
  table,
  isFetching = false,
  fileName,
  showPageNumber = false,
  showExport = true,
}: TablePagesProps<TData>) => {
  const { t } = useTranslation();
  const pageCount = Math.max(1, table.getPageCount());

  return (
    <div>
      <ButtonGroup size="sm" className={pageStyles["button-group"]}>
        {showPageNumber && (
          <Button size="sm" variant="primary">
            {t("Page {{page}} of {{total}}", {
              page: table.atoms.pagination.get().pageIndex + 1,
              total: pageCount,
            })}
          </Button>
        )}
        {isFetching ? (
          renderTooltip(
            t("Refreshing Data"),
            <Button size="sm" variant="primary">
              <i className={`${tableStyles.refreshanimate} fas fa-sync`}></i>
            </Button>
          )
        ) : (
          renderTooltip(
            t("Data Loaded: {{date}}", { date: formatDate(new Date().toISOString()) }),
            <Button size="sm" variant="primary">
              <i className="far fa-check-circle"></i>
            </Button>
          )
        )}
        {showExport && (
          <Button
            size="sm"
            variant="primary"
            onClick={() => exportToCSV(table, fileName ?? "ExportedData.csv")}
          >
            {t("Export Table to CSV")}
          </Button>
        )}
      </ButtonGroup>
    </div>
  );
};

export default BasePages;
