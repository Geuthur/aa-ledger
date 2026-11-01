// Third Party
import type { RowData, Table as TanStackTable } from "@tanstack/react-table";
import { Form } from "react-bootstrap";
import { useTranslation } from "react-i18next";

import type { BaseTableFeatures } from "@/Components/Base/BaseTable/tableFeatures";

export interface BaseTableFormProps<TData extends RowData> {
    table: TanStackTable<BaseTableFeatures, TData>;
}

export function BaseTableForm<TData extends RowData>({ table }: BaseTableFormProps<TData>) {
    const { t } = useTranslation();
    return (
        <div className="d-flex align-items-center ms-2">
          <Form.Label className="m-0 me-2 text-nowrap">{t("Page Size:")}</Form.Label>
          <Form.Select
            className="w-auto"
            value={table.atoms.pagination.get().pageSize}
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
