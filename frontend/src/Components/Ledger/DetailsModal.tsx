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
import RefTypeBadges from "@/Components/Ledger/RefTypeBadges";
import RefTypesModal from "@/Components/Ledger/RefTypesModal";
import ErrorLoader from "@/Components/Loader/ErrorLoader";
import FetchingLoader from "@/Components/Loader/FetchingLoader";
import { BaseTable } from "@/Components/Tables/BaseTable";
import { amountClass, formatIsk } from "@/Utils/ledger";
import { filterCategories, filterRefTypes, formatRefType, sumRefTypes } from "@/Utils/refTypes";

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
  const [search, setSearch] = useState("");
  const [refTypesOf, setRefTypesOf] = useState<CategorySchema | null>(null);

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
          header: t("Reference Types"),
          cell: ({ row }) => (
            <RefTypeBadges
              refTypes={filterRefTypes(row.original.ref_types ?? [], search)}
              showAmounts={search.trim() !== ""}
              onShowAll={() => setRefTypesOf(row.original)}
            />
          ),
        }),
      ] as ColumnDef<CategorySchema, unknown>[],
    [t, search],
  );

  const rows = useMemo(() => filterCategories(data?.[period] ?? [], search), [data, period, search]);
  const matches = useMemo(() => sumRefTypes(rows, search), [rows, search]);
  const matchTotal = matches.reduce((sum, item) => sum + item.amount, 0);

  const periods: { key: Period; label: string }[] = [
    { key: "summary", label: t("Summary") },
    { key: "daily", label: t("Daily") },
    { key: "hourly", label: t("Hourly") },
  ];

  return (
    <Modal
      show={entityId !== null}
      onHide={onHide}
      onExited={() => setSearch("")}
      size="xl"
      centered
      restoreFocus={false}
    >
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
            <input
              type="search"
              className="lg-select lg-input w-100 my-3"
              placeholder={t("Search reference type")}
              aria-label={t("Search reference type")}
              value={search}
              onChange={(event) => setSearch(event.target.value)}
            />
            {search.trim() !== "" && (
              <div className="lg-chord-details mb-3" role="region" aria-label={t("Matching reference types")}>
                {matches.length === 0 ? (
                  <span className="text-muted">{t("No matching reference types")}</span>
                ) : (
                  <>
                    <ul className="list-unstyled m-0">
                      {matches.map((item) => (
                        <li key={item.ref_type} className="lg-chord-flow">
                          <span className="flex-grow-1">{formatRefType(item.ref_type)}</span>
                          <span className={amountClass(item.amount)}>{formatIsk(item.amount)}</span>
                        </li>
                      ))}
                    </ul>
                    <div className="d-flex justify-content-between fw-bold border-top mt-2 pt-2">
                      <span>{t("Total of the matches")}</span>
                      <span className={amountClass(matchTotal)}>{formatIsk(matchTotal)}</span>
                    </div>
                  </>
                )}
              </div>
            )}
            <BaseTable
              columns={columns}
              data={rows}
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
      <RefTypesModal category={refTypesOf} initialSearch={search} onHide={() => setRefTypesOf(null)} />
    </Modal>
  );
}

export default DetailsModal;
