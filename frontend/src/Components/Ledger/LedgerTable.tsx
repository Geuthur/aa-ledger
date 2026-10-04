// React
import { useMemo } from "react";

// Third Party
import { createColumnHelper } from "@tanstack/react-table";
import type { ColumnDef } from "@tanstack/react-table";
import { Info } from "lucide-react";
import { useTranslation } from "react-i18next";

import type { Section } from "@/Api/schema";
import { BaseTable } from "@/Components/Tables/BaseTable";
import { renderTooltip } from "@/Components/Tables/BaseTable/tableHelper";
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

  const columns = useMemo(() => {
    const amountColumn = (key: "bounty" | "ess" | "miscellaneous" | "costs" | "total", header: string) =>
      columnHelper.accessor(key, {
        header,
        cell: ({ getValue }) => (
          <span className={`text-end d-block ${amountClass(getValue())}`}>
            {formatIsk(getValue())}
          </span>
        ),
      });

    const miningColumn = columnHelper.accessor((row) => row.mining ?? 0, {
      id: "mining",
      header: t("Mining"),
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
          const { icon, name, alts } = row.original;
          const label = (
            <span className="d-inline-flex align-items-center gap-2">
              {icon && <img src={icon} alt="" width={24} height={24} className="rounded-circle" />}
              {name}
              {alts.length > 1 && <span className="badge bg-secondary">{alts.length}</span>}
            </span>
          );
          return alts.length > 1
            ? renderTooltip(alts.map((alt) => alt.character_name).join(", "), label)
            : label;
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
              className="lg-btn lg-btn-primary lg-btn-sm"
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
    <BaseTable
      columns={columns}
      data={rows}
      isFetching={isFetching}
      isError={isError}
      emptyText={t("No ledger entries for the selected period")}
      initialState={{ sorting: [{ id: "total", desc: true }] }}
      exportFileName="ledger.csv"
    />
  );
}

export default LedgerTable;
