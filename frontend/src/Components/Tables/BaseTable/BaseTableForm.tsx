// Third Party
import type { Table as TanStackTable } from "@tanstack/react-table";
import { Form } from "react-bootstrap";
import { useTranslation } from "react-i18next";

// Styles
import styles from "./BaseTableForm.module.css";

export function BaseTableForm<TData>({ table }: { table: TanStackTable<TData> }) {
    const { t } = useTranslation();
    return (
        <div className="d-flex align-items-center ms-2">
          <Form.Label className="m-0 me-2 text-nowrap">{t("Page Size:")}</Form.Label>
          <Form.Select
            className={styles["page-size-select"]}
            value={table.getState().pagination.pageSize}
            onChange={(e) => table.setPageSize(Number(e.target.value))}
          >
            {[15, 30, 60, 100, 1000000].map((_pageSize) => (
              <option key={_pageSize} value={_pageSize}>
                {_pageSize === 1000000
                  ? t("Show All")
                  : t("Show {{pageSize}}", { pageSize: _pageSize })}
              </option>
            ))}
          </Form.Select>
        </div>
    );
}
