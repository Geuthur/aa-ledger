// React
import { useMemo, useState } from "react";

// Third Party
import { createColumnHelper } from "@tanstack/react-table";
import type { ColumnDef } from "@tanstack/react-table";
import { Modal } from "react-bootstrap";
import { useTranslation } from "react-i18next";

import type { CategorySchema, RefTypeAmountSchema } from "@/Api/schema";
import { BaseTable } from "@/Components/Base/BaseTable";
import { amountClass, formatIsk } from "@/Utils/ledger";
import { filterRefTypes, formatRefType } from "@/Utils/refTypes";

const columnHelper = createColumnHelper<RefTypeAmountSchema>();

export interface RefTypesModalProps {
  /** Category whose reference types are listed; `null` keeps the modal closed. */
  category: CategorySchema | null;
  /** Search term the modal starts with, e.g. the one of the details modal. */
  initialSearch?: string;
  onHide: () => void;
  /** Opens the character breakdown for a reference type. */
  onSelectRefType?: (refType: RefTypeAmountSchema) => void;
}

/** All reference types of a category with their amount and share. */
function RefTypesModal({
  category,
  initialSearch = "",
  onHide,
  onSelectRefType,
}: RefTypesModalProps) {
  const { t } = useTranslation();
  const [search, setSearch] = useState(initialSearch);

  const rows = useMemo(
    () => filterRefTypes(category?.ref_types ?? [], search),
    [category, search],
  );
  const categoryTotal = category?.amount ?? 0;
  const shown = rows.reduce((sum, item) => sum + (item.amount ?? 0), 0);

  const columns = useMemo(
    () =>
      [
        columnHelper.accessor((item) => formatRefType(item.ref_type), {
          id: "ref_type",
          header: t("Reference Type"),
          cell: ({ row: { original } }) => {
            const hasCharacters = (original.characters ?? []).length > 0;
            return hasCharacters && onSelectRefType ? (
              <button
                type="button"
                className="badge bg-primary border-0"
                style={{ cursor: "pointer" }}
                onClick={() => onSelectRefType(original)}
                title={t("View character breakdown for {{name}}", {
                  name: formatRefType(original.ref_type),
                })}
              >
                {formatRefType(original.ref_type)}
              </button>
            ) : (
              formatRefType(original.ref_type)
            );
          },
        }),
        columnHelper.accessor((item) => item.amount ?? 0, {
          id: "amount",
          header: t("Amount"),
          meta: { align: "right" },
          sortingFn: (a, b) => Math.abs(a.original.amount ?? 0) - Math.abs(b.original.amount ?? 0),
          cell: ({ getValue }) => (
            <span className={`text-end d-block ${amountClass(getValue())}`}>{formatIsk(getValue())}</span>
          ),
        }),
        columnHelper.accessor((item) => (categoryTotal ? (item.amount ?? 0) / categoryTotal : 0), {
          id: "share",
          header: t("Share"),
          meta: { align: "right" },
          cell: ({ getValue }) => (
            <span className="text-end d-block">{categoryTotal ? `${(getValue() * 100).toFixed(1)}%` : "-"}</span>
          ),
        }),
      ] as ColumnDef<RefTypeAmountSchema, unknown>[],
    [t, categoryTotal, onSelectRefType],
  );

  return (
    <Modal
      show={category !== null}
      onHide={onHide}
      onShow={() => setSearch(initialSearch)}
      size="lg"
      centered
      restoreFocus={false}
    >
      <Modal.Header closeButton>
        <Modal.Title>{category?.name}</Modal.Title>
      </Modal.Header>
      <Modal.Body>
        <input
          type="search"
          className="lg-select lg-input mb-3 w-100"
          placeholder={t("Search reference type")}
          aria-label={t("Search reference type")}
          value={search}
          onChange={(event) => setSearch(event.target.value)}
        />
        <BaseTable
          columns={columns}
          data={rows}
          emptyText={t("No matching reference types")}
          initialState={{ sorting: [{ id: "amount", desc: true }] }}
        />
        <div className="d-flex justify-content-end gap-2 fw-bold mt-2">
          <span>{t("Total")}</span>
          <span className={amountClass(shown)}>{formatIsk(shown)}</span>
        </div>
      </Modal.Body>
      <Modal.Footer>
        <button type="button" className="lg-btn lg-btn-secondary" onClick={onHide}>
          {t("Close")}
        </button>
      </Modal.Footer>
    </Modal>
  );
}

export default RefTypesModal;
