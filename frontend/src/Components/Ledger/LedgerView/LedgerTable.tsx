// React
import { useMemo, useState } from "react";

// Third Party
import { Info } from "lucide-react";
import { Button, Form } from "react-bootstrap";
import { useTranslation } from "react-i18next";

import type { Section } from "@/Api/schema";
import { BaseTable } from "@/Components/Base/BaseTable";
import { createBaseColumnHelper } from "@/Components/Base/BaseTable/tableFeatures";
import type { BaseColumnDef } from "@/Components/Base/BaseTable/tableFeatures";
import { HelpTooltip } from "@/Components/Base/HelpTooltip";
import MembersModal from "@/Components/Ledger/LedgerView/MembersModal";
import { useStoredToggle } from "@/Hooks/useStoredToggle";
import { renderTooltip } from "@/Utils/bootsTrap";
import { formatIsk } from "@/Utils/format";
import { amountClass, sumRows } from "@/Utils/ledger";
import type { LedgerRow } from "@/Utils/ledger";

const columnHelper = createBaseColumnHelper<LedgerRow>();

export const SHOW_TOTALS_STORAGE_KEY = "ledger.showTableTotals";

export interface LedgerTableProps {
  rows: LedgerRow[];
  /** Label of the first column, e.g. "Character" or "Corporation". */
  nameLabel: string;
  showMining?: boolean;
  isFetching?: boolean;
  isError?: boolean;
  onDetails: (entityId: number, section: Section) => void;
}

function LedgerTable({
  rows,
  nameLabel,
  showMining = false,
  isFetching,
  isError,
  onDetails,
}: LedgerTableProps) {
  const { t } = useTranslation();
  const [membersRow, setMembersRow] = useState<LedgerRow | null>(null);
  const [showTotals, setShowTotals] = useStoredToggle(SHOW_TOTALS_STORAGE_KEY);

  // Same totals as the summary cards: all rows, not only the current page.
  const totals = useMemo(() => sumRows(rows), [rows]);

  const columns = useMemo(() => {
    const amountColumn = (key: "bounty" | "ess" | "miscellaneous" | "costs" | "total", header: string) =>
      columnHelper.accessor(key, {
        header,
        meta: { align: "right" },
        footer: () => (
          <span className={`text-end d-block ${amountClass(totals[key])}`}>
            {formatIsk(totals[key])}
          </span>
        ),
        cell: ({ getValue }) => (
          <span className={`text-end d-block ${amountClass(getValue())}`}>
            {formatIsk(getValue())}
          </span>
        ),
      });

    const miningColumn = columnHelper.accessor((row) => row.mining ?? 0, {
      id: "mining",
      header: () => (
        <span className="d-inline-flex align-items-center gap-1 justify-content-end">
          {t("Mining")}
          <HelpTooltip text={t("This is only an informational value and is not included in calculations.")} />
        </span>
      ),
      meta: { align: "right" },
      footer: () => (
        <span className={`text-end d-block ${amountClass(totals.mining ?? 0, true)}`}>
          {formatIsk(totals.mining ?? 0)}
        </span>
      ),
      cell: ({ getValue }) => (
        <span className={`text-end d-block ${amountClass(getValue(), true)}`}>
          {formatIsk(getValue())}
        </span>
      ),
    });

    return [
      columnHelper.accessor("name", {
        header: nameLabel,
        footer: () => t("Total"),
        cell: ({ row }) => {
          const { icon, name, alts, is_member } = row.original;
          return (
            <span
              className={`d-inline-flex align-items-center gap-2 ${is_member ? "lg-text-member" : ""
                }`}
            >
              {icon && <img src={icon} alt="" width={24} height={24} className="rounded-circle" />}
              {name}
              {is_member && (
                <span className="lg-badge-member">
                  {nameLabel === t("Corporation") ? t("Member Corp") : t("Member")}
                </span>
              )}
              {alts.length > 1 &&
                renderTooltip(
                  t("Show characters"),
                  <button
                    type="button"
                    className="badge bg-secondary border-0"
                    aria-label={t("Show characters of {{name}}", { name })}
                    onClick={() => setMembersRow(row.original)}
                  >
                    {alts.length}
                  </button>,
                )}
            </span>
          );
        },
      }),
      amountColumn("bounty", t("Bounty")),
      amountColumn("ess", t("ESS")),
      ...(showMining ? [miningColumn] : []),
      amountColumn("miscellaneous", t("Miscellaneous")),
      amountColumn("costs", t("Costs")),
      amountColumn("total", t("Total")),
      columnHelper.display({
        id: "details",
        header: "",
        cell: ({ row }) =>
          renderTooltip(
            t("View Details"),
            <Button
              type="button"
              variant="primary"
              size="sm"
              aria-label={t("View Details")}
              onClick={() => onDetails(row.original.id, "single")}
            >
              <Info size={14} />
            </Button>,
          ),
      }),
    ] as BaseColumnDef<LedgerRow, unknown>[];
  }, [t, nameLabel, showMining, onDetails, totals]);

  return (
    <>
      <div className="d-flex justify-content-end">
        <Form.Check
          type="switch"
          id="ledger-show-totals"
          label={t("Show totals row")}
          checked={showTotals}
          onChange={(event) => setShowTotals(event.currentTarget.checked)}
        />
      </div>
      <BaseTable
        columns={columns}
        data={rows}
        isFetching={isFetching}
        isError={isError}
        emptyText={t("No ledger entries for the selected period")}
        initialState={{ sorting: [{ id: "total", desc: true }] }}
        exportFileName="ledger.csv"
        getRowClassName={(row) => (row.original.is_member ? "lg-table-row-member" : "")}
        showFooter={showTotals}
      />
      <MembersModal row={membersRow} onHide={() => setMembersRow(null)} />
    </>
  );
}

export default LedgerTable;
