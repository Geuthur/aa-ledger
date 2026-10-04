// React
import { useMemo, useState } from "react";

// Third Party
import { useQuery } from "@tanstack/react-query";
import type { QueryKey } from "@tanstack/react-query";
import { createColumnHelper } from "@tanstack/react-table";
import type { ColumnDef } from "@tanstack/react-table";
import { Modal, Nav } from "react-bootstrap";
import { useTranslation } from "react-i18next";

import type { CategorySchema, LedgerDetailsResponse } from "@/Api/schema";
import ErrorLoader from "@/Components/Loader/ErrorLoader";
import FetchingLoader from "@/Components/Loader/FetchingLoader";
import { BaseTable } from "@/Components/Tables/BaseTable";
import { renderTooltip } from "@/Components/Tables/BaseTable/tableHelper";
import { amountClass, formatIsk } from "@/Utils/ledger";

type Period = "summary" | "daily" | "hourly";

const columnHelper = createColumnHelper<CategorySchema>();

export interface DetailsModalProps {
  /** Entity whose details are shown; `null` keeps the modal closed. */
  entityId: number | null;
  title: string;
  queryKey: QueryKey;
  queryFn: () => Promise<LedgerDetailsResponse>;
  onHide: () => void;
}

function DetailsModal({ entityId, title, queryKey, queryFn, onHide }: DetailsModalProps) {
  const { t } = useTranslation();
  const [period, setPeriod] = useState<Period>("summary");

  const { data, isFetching, isError, error } = useQuery({
    queryKey,
    queryFn,
    enabled: entityId !== null,
  });

  const columns = useMemo(
    () =>
      [
        columnHelper.accessor("name", { header: t("Category") }),
        columnHelper.accessor("amount", {
          header: t("Amount"),
          cell: ({ getValue }) => (
            <span className={`text-end d-block ${amountClass(getValue())}`}>
              {formatIsk(getValue())}
            </span>
          ),
        }),
        columnHelper.accessor("average", {
          header: t("Average"),
          cell: ({ getValue }) => (
            <span className="text-end d-block">{formatIsk(getValue())}</span>
          ),
        }),
        columnHelper.accessor("average_tick", {
          header: t("Average per Tick"),
          cell: ({ getValue }) => (
            <span className="text-end d-block">{formatIsk(getValue())}</span>
          ),
        }),
        columnHelper.display({
          id: "ref_types",
          header: t("Included Reference Types"),
          cell: ({ row }) => {
            const refTypes = row.original.ref_types ?? [];
            return renderTooltip(
              refTypes.join(", "),
              <span className="badge bg-secondary">{refTypes.length}</span>,
            );
          },
        }),
      ] as ColumnDef<CategorySchema, unknown>[],
    [t],
  );

  const periods: { key: Period; label: string }[] = [
    { key: "summary", label: t("Summary") },
    { key: "daily", label: t("Daily") },
    { key: "hourly", label: t("Hourly") },
  ];

  return (
    <Modal show={entityId !== null} onHide={onHide} size="xl" centered restoreFocus={false}>
      <Modal.Header closeButton>
        <Modal.Title>{title}</Modal.Title>
      </Modal.Header>
      <Modal.Body>
        {isFetching && <FetchingLoader message={t("Loading...")} />}
        {isError && (
          <ErrorLoader
            title={t("Error")}
            message={error instanceof Error ? error.message : t("Failed to load the details")}
          />
        )}
        {!isFetching && !isError && data && (
          <>
            <Nav variant="tabs" activeKey={period} onSelect={(key) => setPeriod(key as Period)}>
              {periods.map(({ key, label }) => (
                <Nav.Item key={key}>
                  <Nav.Link eventKey={key}>{label}</Nav.Link>
                </Nav.Item>
              ))}
            </Nav>
            <BaseTable
              columns={columns}
              data={data[period]}
              emptyText={t("No data for the selected period")}
              exportFileName="ledger-details.csv"
            />
            <div className="d-flex justify-content-end gap-2 fw-bold mt-2">
              <span>{t("Total")}</span>
              <span className={amountClass(data.total[period])}>
                {formatIsk(data.total[period])}
              </span>
            </div>
          </>
        )}
      </Modal.Body>
    </Modal>
  );
}

export default DetailsModal;
