// React
import { useMemo, useState } from "react";

// Third Party
import { AlertTriangle, RotateCw, Trash2, UserRoundXIcon, Users } from "lucide-react";
import { Alert, Button, Card } from "react-bootstrap";
import { useTranslation } from "react-i18next";

// Styles
import styles from "@/Components/Base/BaseSettings/Settings.module.css";

// AA Base
import { BaseModal } from "@/Components/Base/BaseModal";
import {
  OwnerFilterBar,
  type OwnerTypeFilter,
} from "@/Components/Base/BaseSettings/FilterBar";
import { MissingOwnerCard } from "@/Components/Base/BaseSettings/MissingOwnerCard";
import { BaseOwnerCard } from "@/Components/Base/BaseSettings/OwnerCard";
import type {
  BaseMissingOwner,
  BaseOwner,
  BaseOwnerSettingsSectionProps,
} from "@/Components/Base/BaseSettings/types";

/**
 * Reusable owner overview for the Settings page: header with "Update All", feedback alert,
 * owner grid, missing (unregistered) owners and the delete confirmation modal.
 * Project specific parts are injected via renderCustomCardContent / renderCardActions.
 */
export function BaseOwnerSettingsSection<
  T extends BaseOwner = BaseOwner,
  M extends BaseMissingOwner = BaseMissingOwner,
>({
  title,
  description,
  icon,
  owners,
  missingOwners,
  isLoading = false,
  isError = false,
  errorMessage,
  emptyMessage,
  appName = "Alliance Auth",
  enableFilters = true,
  searchPlaceholder,
  onUpdateAll,
  isUpdatingAll = false,
  globalCooldown = 0,
  feedbackMessage,
  onDismissFeedback,
  onTriggerSingleUpdate,
  isUpdatable,
  isDeletable,
  updatingOwnerId = null,
  ownerCooldowns = {},
  onDeleteOwner,
  isDeleting = false,
  deleteModalTitle,
  deleteModalDescription,
  renderCustomCardContent,
  renderCardActions,
  missingSectionTitle,
  missingActionUrl,
  missingActionLabel,
}: BaseOwnerSettingsSectionProps<T, M>) {
  const { t } = useTranslation();
  const [ownerToDelete, setOwnerToDelete] = useState<T | null>(null);

  const hasOwners = (owners?.length ?? 0) > 0;
  const hasMissing = (missingOwners?.length ?? 0) > 0;

  const [search, setSearch] = useState("");
  const [typeFilter, setTypeFilter] = useState<OwnerTypeFilter>("all");
  const isFiltering = search.trim() !== "" || typeFilter !== "all";

  const counts = useMemo(() => {
    const result: Record<OwnerTypeFilter, number> = {
      all: 0,
      character: 0,
      corporation: 0,
      alliance: 0,
    };
    for (const o of owners ?? []) {
      result.all += 1;
      const type = o.owner_type as OwnerTypeFilter | undefined;
      if (type && type !== "all" && type in result) result[type] += 1;
    }
    for (const m of missingOwners ?? []) {
      result.all += 1;
      const type = (m.owner_type ?? "character") as OwnerTypeFilter;
      if (type !== "all" && type in result) result[type] += 1;
    }
    return result;
  }, [owners, missingOwners]);

  const matchesSearch = (o: { name: string; subtitle?: string | null }) => {
    const q = search.trim().toLowerCase();
    if (!q) return true;
    return (
      o.name.toLowerCase().includes(q) ||
      (o.subtitle ?? "").toLowerCase().includes(q)
    );
  };

  const filteredOwners = useMemo(
    () =>
      (owners ?? []).filter(
        (o) => (typeFilter === "all" || o.owner_type === typeFilter) && matchesSearch(o),
      ),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [owners, typeFilter, search],
  );

  const filteredMissing = useMemo(
    () =>
      (missingOwners ?? []).filter(
        (m) =>
          (typeFilter === "all" || (m.owner_type ?? "character") === typeFilter) &&
          matchesSearch(m),
      ),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [missingOwners, typeFilter, search],
  );

  const hasVisible = filteredOwners.length > 0 || filteredMissing.length > 0;

  const resetFilters = () => {
    setSearch("");
    setTypeFilter("all");
  };

  const handleDeleteConfirm = async () => {
    if (ownerToDelete && onDeleteOwner) {
      await onDeleteOwner(ownerToDelete);
      setOwnerToDelete(null);
    }
  };

  return (
    <Card className={`${styles["section"]} border-0`}>
      <Card.Body className="bg-dark text-light">
        <Card.Header
          className={`${styles["section-header"]} bg-secondary d-flex justify-content-between align-items-center flex-wrap gap-2 rounded`}
        >
          <div>
            <div className={styles["section-title-wrap"]}>
              {icon ?? <Users size={20} aria-hidden="true" />}
              <h2 className={styles["section-title"]}>{title ?? t("Owner Status")}</h2>
              {owners && (
                <span className={styles["section-count"]}>
                  ({isFiltering ? `${filteredOwners.length} / ${owners.length}` : owners.length})
                </span>
              )}
            </div>
            <p className={`${styles["section-description"]} text-light`}>
              {description ?? t("ESI synchronization status of your linked owners.")}
            </p>
          </div>

          {onUpdateAll && hasOwners && (
            <Button
              variant="secondary"
              size="sm"
              className="d-flex align-items-center gap-1"
              disabled={isUpdatingAll || globalCooldown > 0}
              onClick={onUpdateAll}
            >
              {isUpdatingAll ? (
                <span className="spinner-border spinner-border-sm" />
              ) : (
                <RotateCw size={14} />
              )}
              <span>
                {globalCooldown > 0
                  ? t("Update All ({{seconds}}s)", { seconds: globalCooldown })
                  : t("Update All")}
              </span>
            </Button>
          )}
        </Card.Header>

        {feedbackMessage && (
          <Alert
            variant={feedbackMessage.variant}
            className="py-2 mb-3"
            dismissible={Boolean(onDismissFeedback)}
            onClose={onDismissFeedback}
          >
            {feedbackMessage.text}
          </Alert>
        )}

        {enableFilters && !isLoading && !isError && (hasOwners || hasMissing) && (
          <OwnerFilterBar
            search={search}
            onSearchChange={setSearch}
            typeFilter={typeFilter}
            onTypeChange={setTypeFilter}
            counts={counts}
            searchPlaceholder={searchPlaceholder}
          />
        )}

        {isLoading && (
          <div className="aa-loader-container">
            <span className="spinner-border" />
            <span>{t("Loading update statuses...")}</span>
          </div>
        )}

        {isError && (
          <Card className="bg-secondary border-0 shadow-sm" role="alert">
            <Card.Body className={styles["error"]}>
              {errorMessage ?? t("Failed to load update status.")}
            </Card.Body>
          </Card>
        )}

        {!isLoading && !isError && !hasOwners && !hasMissing && (
          <Card className="bg-secondary text-light border-0 shadow-sm">
            <Card.Body className={styles["empty-state"]}>
              {emptyMessage ?? t("Nothing to show.")}
            </Card.Body>
          </Card>
        )}

        {!isLoading && !isError && (hasOwners || hasMissing) && !hasVisible && (
          <Card className="bg-secondary text-light border-0 shadow-sm">
            <Card.Body className={styles["empty-state"]}>
              <p className="mb-2">{t("No matching owners found.")}</p>
              <Button variant="outline-light" size="sm" onClick={resetFilters}>
                {t("Reset filters")}
              </Button>
            </Card.Body>
          </Card>
        )}

        {!isLoading && !isError && filteredOwners.length > 0 && (
          <div className={styles["characters-grid"]}>
            {filteredOwners.map((owner) => (
              <BaseOwnerCard<T>
                key={`${owner.owner_type ?? "owner"}-${owner.id}`}
                owner={owner}
                isUpdating={updatingOwnerId === owner.id}
                cooldown={ownerCooldowns[owner.id] ?? 0}
                onTriggerUpdate={
                  !isUpdatable || isUpdatable(owner) ? onTriggerSingleUpdate : undefined
                }
                onDeleteClick={
                  onDeleteOwner && (!isDeletable || isDeletable(owner))
                    ? setOwnerToDelete
                    : undefined
                }
                renderCustomContent={renderCustomCardContent}
                renderActions={renderCardActions}
              />
            ))}
          </div>
        )}

        {!isLoading && !isError && filteredMissing.length > 0 && (
          <>
            <Card.Header className={`mt-4 mb-2 rounded ${styles["section-title-wrap"]}`}>
              <div>
                <div className={styles["section-title-wrap"]}>
                  <UserRoundXIcon size={20} aria-hidden="true" />
                  <h2 className={styles["section-title"]}>
                    {missingSectionTitle ?? t("Missing in {{app}}", { app: appName })}
                  </h2>
                  {filteredMissing.length > 0 && (
                    <span className={styles["section-count"]}>
                      ({filteredMissing.length})
                    </span>
                  )}
                </div>
                <p className={`${styles["section-description"]} text-light`}>
                  {t("The following characters belong to you but are not registered.")}
                </p>
              </div>
            </Card.Header>
            <div className={styles["characters-grid"]}>
              {filteredMissing.map((missing) => (
                <MissingOwnerCard
                  key={missing.id}
                  missing={missing}
                  appName={appName}
                  actionUrl={missingActionUrl}
                  actionLabel={missingActionLabel} />
              ))}
            </div>
          </>
        )}

        {onDeleteOwner && (
          <BaseModal
            show={Boolean(ownerToDelete)}
            onHide={() => !isDeleting && setOwnerToDelete(null)}
            centered
            title={
              <div className="d-flex align-items-center gap-2 text-danger">
                <Trash2 size={20} />
                <span>{deleteModalTitle ?? t("Delete Owner")}</span>
              </div>
            }
            footer={
              <div className="d-flex align-items-center justify-content-end gap-2 w-100">
                <Button
                  variant="secondary"
                  onClick={() => setOwnerToDelete(null)}
                  disabled={isDeleting}
                >
                  {t("Cancel")}
                </Button>
                <Button
                  variant="danger"
                  onClick={handleDeleteConfirm}
                  disabled={isDeleting}
                  className="d-flex align-items-center gap-1"
                >
                  <Trash2 size={14} />
                  <span>{isDeleting ? t("Deleting...") : t("Confirm Delete")}</span>
                </Button>
              </div>
            }
          >
            <div className="p-3 d-flex align-items-start gap-3">
              <AlertTriangle className="text-danger flex-shrink-0 mt-1" size={24} />
              <div>
                <p className="fw-semibold mb-1">
                  {t("Are you sure you want to delete owner '{{name}}'?", {
                    name: ownerToDelete?.name,
                  })}
                </p>
                <div className="small text-muted">
                  {ownerToDelete && deleteModalDescription
                    ? deleteModalDescription(ownerToDelete)
                    : t("This action cannot be undone.")}
                </div>
              </div>
            </div>
          </BaseModal>
        )}
      </Card.Body>
    </Card>
  );
}
