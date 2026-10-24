// React
import React, { useMemo } from "react";

// Third Party
import { createColumnHelper } from "@tanstack/react-table";
import type { ColumnDef } from "@tanstack/react-table";
import { RefreshCw, User } from "lucide-react";
import { Button, ButtonGroup, Dropdown, Spinner } from "react-bootstrap";
import { useTranslation } from "react-i18next";

// Styles
import styles from "@/Styles/modules/Administration.module.css";

// AA Ledger
import type { AltSchema, AdministrationOwnerSchema } from "@/Api/schema";
import BaseModal, { ModalSize } from "@/Components/Base/BaseModal";
import { BaseTable } from "@/Components/Base/BaseTable";

export interface AdministrationAltsModalProps {
  owner: AdministrationOwnerSchema | null;
  updatingKey: string | null;
  isSuperuser?: boolean;
  onHide: () => void;
  onTriggerUpdate: (
    ownerType: "character" | "corporation",
    ownerId: number,
    forceRefresh: boolean,
  ) => void;
}

export const AdministrationAltsModal: React.FC<AdministrationAltsModalProps> = ({
  owner,
  updatingKey,
  isSuperuser = false,
  onHide,
  onTriggerUpdate,
}) => {
  const { t } = useTranslation();

  const isUpdating = Boolean(
    owner && updatingKey === `${owner.owner_type}-${owner.owner_id}`,
  );

  const columns = useMemo<ColumnDef<AltSchema, unknown>[]>(() => {
    const columnHelper = createColumnHelper<AltSchema>();

    return [
      columnHelper.display({
        id: "avatar",
        header: () => null,
        size: 40,
        enableSorting: false,
        cell: ({ row }) => {
          const alt = row.original;
          return alt.icon ? (
            <img
              src={alt.icon}
              alt=""
              width={28}
              height={28}
              className="rounded-circle"
              loading="lazy"
            />
          ) : (
            <div
              className={`p-1 bg-secondary rounded text-center ${styles.avatarFallback}`}
            >
              <User size={14} />
            </div>
          );
        },
      }),

      columnHelper.accessor("character_name", {
        id: "character_name",
        header: t("Character"),
        cell: ({ row }) => {
          const alt = row.original;
          return (
            <div>
              <div className="fw-semibold">{alt.character_name}</div>
              {alt.ticker && (
                <span className="text-muted small">[{alt.ticker}]</span>
              )}
            </div>
          );
        },
      }),

      columnHelper.accessor("character_id", {
        id: "character_id",
        header: t("Character ID"),
        cell: ({ getValue }) => (
          <span className="text-muted small font-monospace">{getValue()}</span>
        ),
      }),
    ];
  }, [t]);

  const alts = owner?.alts ?? [];

  return (
    <BaseModal
      show={owner !== null}
      onHide={onHide}
      size={ModalSize.large}
      titleClassName="d-flex align-items-center gap-2"
      title={
        <>
          {owner?.icon && (
            <img
              src={owner.icon}
              alt=""
              width={28}
              height={28}
              className="rounded-circle"
            />
          )}
          <span>{owner?.name}</span>
          <span className="text-muted small ms-1">
            ({alts.length} {t("Alts")})
          </span>
        </>
      }
    >
      <div>
        <div className="d-flex align-items-center justify-content-between mb-3 pb-2 border-bottom">
          <div className="text-muted small">
            {t("Manage and update all characters for this owner.")}
          </div>
          {owner && (
            <Dropdown as={ButtonGroup} size="sm">
              <Button
                variant="danger"
                size="sm"
                disabled={isUpdating}
                onClick={() =>
                  onTriggerUpdate("character", owner.owner_id, false)
                }
                className="d-inline-flex align-items-center gap-1"
                data-testid={`update-all-alts-btn-${owner.owner_id}`}
              >
                {isUpdating ? (
                  <Spinner size="sm" animation="border" />
                ) : (
                  <RefreshCw size={13} />
                )}
                <span>{t("Update All Alts")}</span>
              </Button>
              <Dropdown.Toggle
                split
                size="sm"
                variant="danger"
                aria-label={t("More update options")}
                disabled={isUpdating}
              />
              <Dropdown.Menu
                align="end"
                className={`shadow-lg ${styles.dropdownMenu}`}
              >
                <Dropdown.Item
                  onClick={() =>
                    onTriggerUpdate("character", owner.owner_id, false)
                  }
                >
                  <RefreshCw size={14} className="me-2 text-primary" />
                  {t("Normal Update")}
                </Dropdown.Item>
                {isSuperuser && (
                  <Dropdown.Item
                    onClick={() =>
                      onTriggerUpdate("character", owner.owner_id, true)
                    }
                  >
                    <RefreshCw size={14} className="me-2 text-warning" />
                    {t("Force Refresh (Bypass Cache)")}
                  </Dropdown.Item>
                )}
              </Dropdown.Menu>
            </Dropdown>
          )}
        </div>

        <BaseTable
          columns={columns}
          data={alts}
          emptyText={t("No alt characters found.")}
          initialState={{ sorting: [{ id: "character_name", desc: false }] }}
        />
      </div>
    </BaseModal>
  );
};

export default AdministrationAltsModal;
