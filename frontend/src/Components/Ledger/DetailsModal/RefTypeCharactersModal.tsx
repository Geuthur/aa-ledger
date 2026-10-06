// React
import { useMemo, useState } from "react";

// Third Party
import { createColumnHelper } from "@tanstack/react-table";
import type { ColumnDef } from "@tanstack/react-table";
import { Button, Modal } from "react-bootstrap";
import { useTranslation } from "react-i18next";

import type { CharacterRefTypeSchema, RefTypeAmountSchema } from "@/Api/schema";
import { BaseTable } from "@/Components/Base/BaseTable";
import { amountClass, formatIsk } from "@/Utils/ledger";
import { formatRefType } from "@/Utils/refTypes";

const columnHelper = createColumnHelper<CharacterRefTypeSchema>();

export interface RefTypeCharactersModalProps {
  /** Reference type whose characters are listed; `null` keeps the modal closed. */
  refType: RefTypeAmountSchema | null;
  onHide: () => void;
}

/** The characters that contributed to or spent from a reference type. */
function RefTypeCharactersModal({ refType, onHide }: RefTypeCharactersModalProps) {
  const { t } = useTranslation();
  const [search, setSearch] = useState("");

  const characterCount = refType?.characters?.length ?? 0;
  const refTypeTotal = refType?.amount ?? 0;

  const rows = useMemo(() => {
    const list = refType?.characters ?? [];
    const needle = search.trim().toLowerCase();
    if (!needle) return list;
    return list.filter((c) => c.character_name.toLowerCase().includes(needle));
  }, [refType?.characters, search]);

  const shownTotal = rows.reduce((sum, item) => sum + (item.amount ?? 0), 0);

  const columns = useMemo(
    () =>
      [
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
        columnHelper.accessor("amount", {
          header: t("Amount"),
          meta: { align: "right" },
          sortingFn: (a, b) => Math.abs(a.original.amount ?? 0) - Math.abs(b.original.amount ?? 0),
          cell: ({ getValue }) => (
            <span className={`text-end d-block ${amountClass(getValue())}`}>{formatIsk(getValue())}</span>
          ),
        }),
        columnHelper.accessor((item) => (refTypeTotal ? Math.abs(item.amount / refTypeTotal) : 0), {
          id: "share",
          header: t("Share"),
          meta: { align: "right" },
          cell: ({ getValue }) => {
            const val = getValue() as number;
            return (
              <span className="text-end d-block">
                {refTypeTotal ? `${(val * 100).toFixed(1)}%` : "-"}
              </span>
            );
          },
        }),
      ] as ColumnDef<CharacterRefTypeSchema, unknown>[],
    [t, refTypeTotal],
  );

  return (
    <Modal
      show={refType !== null}
      onHide={onHide}
      onExited={() => setSearch("")}
      size="lg"
      centered
      restoreFocus={false}
    >
      <Modal.Header closeButton>
        <Modal.Title>{refType ? formatRefType(refType.ref_type) : ""}</Modal.Title>
      </Modal.Header>
      <Modal.Body>
        <div className="aa-panel">
          {characterCount > 5 && (
            <input
              type="search"
              className="lg-select lg-input mb-3 w-100"
              placeholder={t("Search character")}
              aria-label={t("Search character")}
              value={search}
              onChange={(event) => setSearch(event.target.value)}
            />
          )}
          <BaseTable
            variant="vowra-light"
            columns={columns}
            data={rows}
            emptyText={t("No characters")}
            initialState={{ sorting: [{ id: "amount", desc: true }] }}
          />
          <div className="d-flex justify-content-end gap-2 fw-bold mt-2">
            <span>{t("Total")}</span>
            <span className={amountClass(shownTotal)}>{formatIsk(shownTotal)}</span>
          </div>
        </div>
      </Modal.Body>
      <Modal.Footer>
        <Button variant="primary" onClick={onHide}>
          {t("Close")}
        </Button>
      </Modal.Footer>
    </Modal>
  );
}

export default RefTypeCharactersModal;
