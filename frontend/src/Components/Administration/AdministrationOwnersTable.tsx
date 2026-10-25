// React
import React, { useMemo, useState } from "react";

// Third Party
import { useQuery } from "@tanstack/react-query";
import { createColumnHelper } from "@tanstack/react-table";
import type { ColumnDef } from "@tanstack/react-table";
import { Building2, Eye, RefreshCw, Shield, Trash2, User } from "lucide-react";
import { Badge, Button, ButtonGroup, Card, Dropdown, Spinner } from "react-bootstrap";
import { useTranslation } from "react-i18next";

// Styles
import styles from "@/Styles/modules/Administration.module.css";

// AA Ledger
import { loadSettingsUnregistered } from "@/Api/ApiCalls";
import { queryKeys } from "@/Api/query";
import type { AdministrationOwnerSchema } from "@/Api/schema";
import { AdministrationAltsModal } from "@/Components/Administration/AdministrationAltsModal";
import { AdministrationErrorModal } from "@/Components/Administration/AdministrationErrorModal";
import { UnregisteredModal } from "@/Components/Base/BaseSettings";
import { BaseTable } from "@/Components/Base/BaseTable";
import ErrorLoader from "@/Components/Base/Loader/ErrorLoader";
import FetchingLoader from "@/Components/Base/Loader/FetchingLoader";
import { renderTooltip } from "@/Utils/bootsTrap";
import { formatRelativeTime } from "@/Utils/format";

interface AdministrationOwnersTableProps {
  owners?: AdministrationOwnerSchema[];
  isLoading: boolean;
  isError: boolean;
  updatingKey: string | null;
  isSuperuser?: boolean;
  onInspect: (owner: AdministrationOwnerSchema) => void;
  onTriggerUpdate: (ownerType: "character" | "corporation", ownerId: number, forceRefresh: boolean) => void;
  onDelete: (owner: AdministrationOwnerSchema) => void;
}

export const AdministrationOwnersTable: React.FC<AdministrationOwnersTableProps> = ({
  owners,
  isLoading,
  isError,
  updatingKey,
  isSuperuser = false,
  onInspect,
  onTriggerUpdate,
  onDelete,
}) => {
  const { t } = useTranslation();
  const [selectedAltsOwner, setSelectedAltsOwner] = useState<AdministrationOwnerSchema | null>(null);
  const [selectedErrorOwner, setSelectedErrorOwner] = useState<AdministrationOwnerSchema | null>(null);
  const [selectedUnregisteredOwner, setSelectedUnregisteredOwner] = useState<AdministrationOwnerSchema | null>(null);

  const {
    data: unregisteredData,
    isLoading: isLoadingUnregistered,
    isError: isErrorUnregistered,
  } = useQuery({
    queryKey: selectedUnregisteredOwner
      ? queryKeys.SettingsUnregistered(
          selectedUnregisteredOwner.owner_type,
          selectedUnregisteredOwner.owner_id,
        )
      : ["settings", "unregistered", "disabled"],
    queryFn: () =>
      loadSettingsUnregistered(
        selectedUnregisteredOwner!.owner_type,
        selectedUnregisteredOwner!.owner_id,
      ),
    enabled: Boolean(selectedUnregisteredOwner),
  });

  const columns = useMemo<ColumnDef<AdministrationOwnerSchema, unknown>[]>(() => {
    const columnHelper = createColumnHelper<AdministrationOwnerSchema>();

    return [
      columnHelper.display({
        id: "avatar",
        header: () => null,
        size: 48,
        enableSorting: false,
        cell: ({ row }) => {
          const owner = row.original;
          return owner.icon ? (
            <img
              src={owner.icon}
              alt=""
              width={32}
              height={32}
              className={owner.owner_type === "character" ? "rounded" : "rounded-circle"}
              loading="lazy"
            />
          ) : (
            <div className={`p-1 bg-secondary rounded text-center ${styles.avatarFallback}`}>
              {owner.owner_type === "alliance" ? (
                <Shield size={16} />
              ) : owner.owner_type === "corporation" ? (
                <Building2 size={16} />
              ) : (
                <User size={16} />
              )}
            </div>
          );
        },
      }),

      columnHelper.accessor("name", {
        id: "name",
        header: t("Name"),
        cell: ({ row }) => {
          const owner = row.original;
          const altCount = owner.alts?.length ?? 0;
          const unregisteredCount = owner.unregistered_count ?? 0;
          return (
            <div>
              <div className="d-flex align-items-center flex-wrap gap-1">
                <span className="fw-semibold">{owner.name}</span>
                {altCount > 0 && (
                  <Button
                    variant="secondary"
                    size="sm"
                    className={`py-0 px-2 lh-1 text-decoration-none ${styles.compactButton}`}
                    onClick={() => setSelectedAltsOwner(owner)}
                    data-testid={`alts-btn-${owner.owner_type}-${owner.owner_id}`}
                  >
                    {altCount} {t("Alts")}
                  </Button>
                )}
                {unregisteredCount > 0 && (
                  <Button
                    variant="warning"
                    size="sm"
                    className={`py-0 px-2 lh-1 text-decoration-none ${styles.compactButton}`}
                    onClick={() => setSelectedUnregisteredOwner(owner)}
                    data-testid={`unregistered-btn-${owner.owner_type}-${owner.owner_id}`}
                  >
                    {unregisteredCount} {t("Unregistered")}
                  </Button>
                )}
              </div>
              {owner.ticker && (
                <span className="text-muted small">[{owner.ticker}]</span>
              )}
            </div>
          );
        },
      }),

      columnHelper.accessor("owner_type", {
        id: "owner_type",
        header: t("Type"),
        cell: ({ row }) => {
          const owner = row.original;
          let badgeVariant = "info";
          if (owner.owner_type === "corporation") badgeVariant = "primary";
          else if (owner.owner_type === "alliance") badgeVariant = "success";

          return (
            <Badge bg={badgeVariant} className="text-uppercase">
              {owner.owner_type}
            </Badge>
          );
        },
      }),

      columnHelper.accessor("user_name", {
        id: "user_name",
        header: t("Auth User"),
        cell: ({ row }) => {
          const owner = row.original;
          return owner.user_name ? (
            <span className="badge bg-secondary border border-secondary-subtle">
              {owner.user_name}
            </span>
          ) : (
            <span className="text-muted small">-</span>
          );
        },
      }),

      columnHelper.accessor("status", {
        id: "status",
        header: t("Status"),
        cell: ({ row }) => {
          const owner = row.original;
          let badgeVariant = "success";
          if (owner.status === "disabled" || !owner.is_active) badgeVariant = "secondary";
          else if (owner.status === "token_error" || owner.error_message) badgeVariant = "danger";
          else if (owner.status === "warning") badgeVariant = "warning";

          const statusLabel = owner.status || (owner.is_active ? "OK" : "Disabled");
          const hasError = Boolean(owner.error_message) || owner.status === "token_error";

          if (!hasError) {
            return <Badge bg={badgeVariant}>{statusLabel}</Badge>;
          }

          const openError = () => setSelectedErrorOwner(owner);

          return (
            <Badge
              bg={badgeVariant}
              role="button"
              tabIndex={0}
              aria-label={t("Show error details of {{name}}", { name: owner.name })}
              className={styles.statusBadgeClickable}
              onClick={openError}
              onKeyDown={(event: React.KeyboardEvent) => {
                if (event.key === "Enter" || event.key === " ") {
                  event.preventDefault();
                  openError();
                }
              }}
              data-testid={`error-badge-${owner.owner_type}-${owner.owner_id}`}
            >
              {statusLabel}
            </Badge>
          );
        },
      }),

      columnHelper.accessor("last_sync", {
        id: "last_sync",
        header: t("Last sync"),
        cell: ({ row }) => {
          const owner = row.original;
          return owner.last_sync ? (
            <span className="small text-muted">
              {formatRelativeTime(owner.last_sync)}
            </span>
          ) : (
            <span className="text-muted small">{t("Never")}</span>
          );
        },
      }),

      columnHelper.display({
        id: "actions",
        header: () => <div className="text-end">{t("Actions")}</div>,
        size: 160,
        enableSorting: false,
        cell: ({ row }) => {
          const owner = row.original;

          if (owner.owner_type === "alliance") {
            return (
              <div className="d-flex align-items-center justify-content-end gap-2">
                {renderTooltip(
                  t("Inspect Owner"),
                  <Button
                    variant="primary"
                    size="sm"
                    onClick={() => onInspect(owner)}
                    className="d-inline-flex align-items-center gap-1"
                    data-testid={`inspect-btn-${owner.owner_type}-${owner.owner_id}`}
                  >
                    <Eye size={13} />
                    <span>{t("Inspect")}</span>
                  </Button>
                )}
              </div>
            );
          }

          const targetOwnerType = owner.owner_type as "character" | "corporation";
          const isUpdatingThis = updatingKey === `${targetOwnerType}-${owner.owner_id}`;

          return (
            <div className="d-flex align-items-center justify-content-end gap-2">
              {/* Inspect / View Button */}
              {renderTooltip(
                t("Inspect Owner"),
                <Button
                  variant="primary"
                  size="sm"
                  onClick={() => onInspect(owner)}
                  className="d-inline-flex align-items-center gap-1"
                  data-testid={`inspect-btn-${owner.owner_type}-${owner.owner_id}`}
                >
                  <Eye size={13} />
                  <span>{t("Inspect")}</span>
                </Button>
              )}

              {/* Update dropdown: normal & force refresh */}
              <Dropdown as={ButtonGroup} size="sm">
                {renderTooltip(
                  t("Trigger owner update task"),
                  <Button
                    variant="danger"
                    size="sm"
                    disabled={isUpdatingThis}
                    onClick={() => onTriggerUpdate(targetOwnerType, owner.owner_id, false)}
                    className="d-inline-flex align-items-center gap-1"
                    data-testid={`update-btn-${owner.owner_type}-${owner.owner_id}`}
                  >
                    {isUpdatingThis ? (
                      <Spinner size="sm" animation="border" />
                    ) : (
                      <RefreshCw size={13} />
                    )}
                    <span>{t("Update")}</span>
                  </Button>
                )}
                {renderTooltip(
                  t("More update options"),
                  <Dropdown.Toggle
                    split
                    size="sm"
                    variant="danger"
                    aria-label={t("More update options")}
                    disabled={isUpdatingThis}
                    className="aa-react"
                  />
                )}
                <Dropdown.Menu
                  align="end"
                  className={`shadow-lg ${styles.dropdownMenu}`}
                >
                  <Dropdown.Item
                    onClick={() => onTriggerUpdate(targetOwnerType, owner.owner_id, false)}
                  >
                    <RefreshCw size={14} className="me-2 text-primary" />
                    {t("Normal Update")}
                  </Dropdown.Item>
                  {isSuperuser && (
                    <Dropdown.Item
                      onClick={() => onTriggerUpdate(targetOwnerType, owner.owner_id, true)}
                    >
                      <RefreshCw size={14} className="me-2 text-warning" />
                      {t("Force Refresh (Bypass Cache)")}
                    </Dropdown.Item>
                  )}
                </Dropdown.Menu>
              </Dropdown>

              {/* Delete button */}
              {renderTooltip(
                t("Delete Owner"),
                <Button
                  variant="danger"
                  size="sm"
                  onClick={() => onDelete(owner)}
                  className="d-inline-flex align-items-center gap-1"
                  data-testid={`delete-btn-${owner.owner_type}-${owner.owner_id}`}
                >
                  <Trash2 size={13} />
                  <span>{t("Delete")}</span>
                </Button>
              )}
            </div>
          );
        },
      }),
    ];
  }, [t, updatingKey, isSuperuser, onInspect, onTriggerUpdate, onDelete]);

  return (
    <>
      <Card className="mt-3 border-0">
        {isLoading && <FetchingLoader message={t("Loading owners…")} />}
        {isError && <ErrorLoader title={t("Error")} message={t("Failed to load owners")} />}
        {!isLoading && !isError && (
          <BaseTable
            columns={columns}
            data={owners ?? []}
            emptyText={t("No owners found.")}
            exportFileName="administration_owners.csv"
          />
        )}
      </Card>

      <AdministrationAltsModal
        owner={selectedAltsOwner}
        updatingKey={updatingKey}
        isSuperuser={isSuperuser}
        onHide={() => setSelectedAltsOwner(null)}
        onTriggerUpdate={onTriggerUpdate}
      />

      <AdministrationErrorModal
        show={selectedErrorOwner !== null}
        onHide={() => setSelectedErrorOwner(null)}
        ownerName={selectedErrorOwner?.name ?? ""}
        status={selectedErrorOwner?.status ?? ""}
        errorMessage={selectedErrorOwner?.error_message}
      />

      <UnregisteredModal
        show={!!selectedUnregisteredOwner}
        onHide={() => setSelectedUnregisteredOwner(null)}
        title={
          selectedUnregisteredOwner?.owner_type === "alliance"
            ? t("Unregistered corporations of {{name}}", {
                name: selectedUnregisteredOwner.name,
              })
            : t("Unregistered members of {{name}}", {
                name: selectedUnregisteredOwner?.name ?? "",
              })
        }
        description={
          selectedUnregisteredOwner?.owner_type === "alliance"
            ? t("Corporations of this alliance that are not registered in Ledger.")
            : t("Characters of this corporation that are not registered in Ledger.")
        }
        items={unregisteredData?.items ?? []}
        isLoading={isLoadingUnregistered}
        isError={isErrorUnregistered}
        errorMessage={t("Failed to load unregistered entries.")}
        emptyMessage={t("Everything is registered.")}
      />
    </>
  );
};
