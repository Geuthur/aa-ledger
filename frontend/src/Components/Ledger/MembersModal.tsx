// React
import { useMemo } from "react";

// Third Party
import { createColumnHelper } from "@tanstack/react-table";
import type { ColumnDef } from "@tanstack/react-table";
import { CircleHelp } from "lucide-react";
import { Modal } from "react-bootstrap";
import { useTranslation } from "react-i18next";

import type { AltLedgerSchema } from "@/Api/schema";
import { BaseTable } from "@/Components/Tables/BaseTable";
import { renderTooltip } from "@/Components/Tables/BaseTable/tableHelper";
import { amountClass, formatIsk } from "@/Utils/ledger";
import type { LedgerRow } from "@/Utils/ledger";

const columnHelper = createColumnHelper<AltLedgerSchema>();

export interface MembersModalProps {
  /** Entity whose characters are listed; `null` keeps the modal closed. */
  row: LedgerRow | null;
  onHide: () => void;
}

/** The characters of an entity and how much each one contributed to its ledger. */
function MembersModal({ row, onHide }: MembersModalProps) {
  const { t } = useTranslation();
  const members = row?.members ?? [];
  const entityTotal = row?.total ?? 0;

  const columns = useMemo(() => {
    const amountColumn = (key: "bounty" | "ess" | "miscellaneous" | "costs" | "total", header: string) =>
      columnHelper.accessor((member) => member.ledger[key] ?? 0, {
        id: key,
        header,
        meta: { align: "right" },
        cell: ({ getValue }) => (
          <span className={`text-end d-block ${amountClass(getValue())}`}>{formatIsk(getValue())}</span>
        ),
      });

    return [
      columnHelper.accessor("character_name", {
        header: t("Character"),
        cell: ({ row: { original } }) => (
          <span className="d-inline-flex align-items-center gap-2">
            {original.icon && (
              <img src={original.icon} alt="" width={24} height={24} className="rounded-circle" />
            )}
            {original.character_name}
          </span>
        ),
      }),
      amountColumn("bounty", t("Bounty")),
      amountColumn("ess", t("ESS")),
      amountColumn("miscellaneous", t("Miscellaneous")),
      amountColumn("costs", t("Costs")),
      amountColumn("total", t("Total")),
      columnHelper.accessor((member) => (entityTotal ? (member.ledger.total ?? 0) / entityTotal : 0), {
        id: "share",
        header: () => (
          <span className="d-inline-flex align-items-center gap-1 justify-content-end">
            {t("Share")}
            {renderTooltip(
              t(
                "Share of the total net amount. When negative amounts (costs) are involved, shares can exceed 100% or be negative, but always total 100%.",
              ),
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
          <span className="text-end d-block">{entityTotal ? `${(getValue() * 100).toFixed(1)}%` : "-"}</span>
        ),
      }),
    ] as ColumnDef<AltLedgerSchema, unknown>[];
  }, [t, entityTotal]);

  return (
    <Modal show={row !== null} onHide={onHide} size="xl" centered restoreFocus={false}>
      <Modal.Header closeButton>
        <Modal.Title className="d-flex align-items-center gap-2">
          {row?.icon && <img src={row.icon} alt="" width={32} height={32} className="rounded-circle" />}
          {row?.name}
        </Modal.Title>
      </Modal.Header>
      <Modal.Body>
        <BaseTable
          columns={columns}
          data={members}
          emptyText={t("No characters")}
          initialState={{ sorting: [{ id: "total", desc: true }] }}
        />
      </Modal.Body>
      <Modal.Footer>
        <button type="button" className="lg-btn lg-btn-secondary" onClick={onHide}>
          {t("Close")}
        </button>
      </Modal.Footer>
    </Modal>
  );
}

export default MembersModal;
