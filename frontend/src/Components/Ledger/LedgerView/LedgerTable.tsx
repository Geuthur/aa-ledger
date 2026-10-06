// React
import { useMemo, useState } from "react";

// Third Party
import { createColumnHelper } from "@tanstack/react-table";
import type { ColumnDef } from "@tanstack/react-table";
import { CircleHelp, Info } from "lucide-react";
import { useTranslation } from "react-i18next";

import type { Section } from "@/Api/schema";
import { BaseTable } from "@/Components/Base/BaseTable";
import { renderTooltip } from "@/Components/Base/BaseTable/tableHelper";
import MembersModal from "@/Components/Ledger/LedgerView/MembersModal";
import { amountClass, formatIsk } from "@/Utils/ledger";
import type { LedgerRow } from "@/Utils/ledger";

const columnHelper = createColumnHelper<LedgerRow>();

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

  const columns = useMemo(() => {
    const amountColumn = (key: "bounty" | "ess" | "miscellaneous" | "costs" | "total", header: string) =>
      columnHelper.accessor(key, {
        header,
        meta: { align: "right" },
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
          {renderTooltip(
            t("This is only an informational value and is not included in calculations."),
            <span
              className="d-inline-flex align-items-center text-muted"
              style={{ cursor: "help" }}
            >
              <CircleHelp size={14} />
            </span>,
          )}
        </span>
      ),
      meta: { align: "right" },
      cell: ({ getValue }) => (
        <span className={`text-end d-block ${amountClass(getValue(), true)}`}>
          {formatIsk(getValue())}
        </span>
      ),
    });

    return [
      columnHelper.accessor("name", {
        header: nameLabel,
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
            <button
              type="button"
              className="aa-btn aa-btn-primary aa-btn-sm"
              aria-label={t("View Details")}
              onClick={() => onDetails(row.original.id, "single")}
            >
              <Info size={14} />
            </button>,
          ),
      }),
    ] as ColumnDef<LedgerRow, unknown>[];
  }, [t, nameLabel, showMining, onDetails]);

  return (
    <>
      <BaseTable
        columns={columns}
        data={rows}
        isFetching={isFetching}
        isError={isError}
        emptyText={t("No ledger entries for the selected period")}
        initialState={{ sorting: [{ id: "total", desc: true }] }}
        exportFileName="ledger.csv"
        getRowClassName={(row) => (row.original.is_member ? "lg-table-row-member" : "")}
      />
      <MembersModal row={membersRow} onHide={() => setMembersRow(null)} />
    </>
  );
}

export default LedgerTable;
