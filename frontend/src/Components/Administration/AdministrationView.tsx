// React
import { useEffect, useState } from "react";
import type { ReactNode } from "react";
import { Link } from "react-router";

// Third Party
import { useMutation, useQueryClient } from "@tanstack/react-query";
import type { QueryKey } from "@tanstack/react-query";
import { createColumnHelper } from "@tanstack/react-table";
import type { ColumnDef } from "@tanstack/react-table";
import { AlertCircle, AlertTriangle, CheckCircle2, Clock, LogIn, RotateCw, Trash2, UserCheck, UserMinus, UserX, Users, XCircle } from "lucide-react";
import { Alert, Badge, Button, Col, Row, Spinner } from "react-bootstrap";
import { useTranslation } from "react-i18next";

import type { AdminOwnerSchema, AdministrationResponse, AltSchema, MessageSchema } from "@/Api/schema";
import BaseSectionHeader from "@/Components/Base/BaseHeader";
import BaseModal, { ModalSize } from "@/Components/Base/BaseModal";
import { BaseTable } from "@/Components/Base/BaseTable";
import { formatDate, formatRelativeTime, renderTooltip } from "@/Components/Base/BaseTable/tableHelper";
import ErrorLoader from "@/Components/Base/Loader/ErrorLoader";
import FetchingLoader from "@/Components/Base/Loader/FetchingLoader";

const memberColumn = createColumnHelper<AltSchema>();

export interface AdministrationViewProps {
  title: string;
  data?: AdministrationResponse;
  isLoading: boolean;
  error: Error | null;
  /** Singular label of the registered entries, e.g. "Character". */
  entryLabel: string;
  /** Singular label of the missing entries if different from entryLabel, e.g. "Character" when entry is "Corporation". */
  missingLabel?: string;
  queryKey: QueryKey;
  /** Route of the ledger of an entry. */
  ledgerPath: (ownerId: number) => string;
  /** Removes an entry; omit if entries cannot be removed on this page. */
  onDelete?: (ownerId: number) => Promise<MessageSchema>;
  /** Trigger manual update of entries; returns MessageSchema on success */
  onUpdate?: () => Promise<MessageSchema>;
  /** Optional custom action element in the header. */
  headerAction?: ReactNode;
  /** Whether to show "View Ledger" button on each card (default: true). */
  showCardLedger?: boolean;
}

function AdministrationView({
  title,
  data,
  isLoading,
  error,
  entryLabel,
  missingLabel,
  queryKey,
  ledgerPath,
  onDelete,
  onUpdate,
  headerAction,
  showCardLedger = true,
}: AdministrationViewProps) {
  const { t } = useTranslation();
  const queryClient = useQueryClient();
  const [pending, setPending] = useState<AdminOwnerSchema | null>(null);
  const [message, setMessage] = useState<{ variant: "success" | "danger"; text: string } | null>(
    null,
  );
  const [prevCooldownProp, setPrevCooldownProp] = useState<number | undefined>(
    data?.cooldown_seconds,
  );
  const [cooldown, setCooldown] = useState<number>(data?.cooldown_seconds ?? 0);

  if (data?.cooldown_seconds !== prevCooldownProp) {
    setPrevCooldownProp(data?.cooldown_seconds);
    setCooldown(data?.cooldown_seconds ?? 0);
  }

  useEffect(() => {
    if (cooldown <= 0) return;
    const timer = setInterval(() => {
      setCooldown((prev) => (prev > 0 ? prev - 1 : 0));
    }, 1000);
    return () => clearInterval(timer);
  }, [cooldown]);

  const remove = useMutation({
    mutationFn: (ownerId: number) => (onDelete ? onDelete(ownerId) : Promise.reject()),
    onSuccess: (result) => {
      setMessage({ variant: "success", text: result.message });
      return queryClient.invalidateQueries({ queryKey });
    },
    onError: (failure: Error) => setMessage({ variant: "danger", text: failure.message }),
    onSettled: () => setPending(null),
  });

  const update = useMutation({
    mutationFn: () => (onUpdate ? onUpdate() : Promise.reject()),
    onSuccess: (result) => {
      setMessage({ variant: "success", text: result.message });
      return queryClient.invalidateQueries({ queryKey });
    },
    onError: (failure: Error) => setMessage({ variant: "danger", text: failure.message }),
  });

  const formatCooldown = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, "0")}`;
  };

  const memberColumns = [
    memberColumn.accessor("character_name", {
      header: t("Character"),
      cell: ({ row }) => (
        <span className="d-inline-flex align-items-center gap-2">
          {row.original.icon && (
            <img src={row.original.icon} alt="" width={32} height={32} className="rounded-circle" />
          )}
          {row.original.character_name}
        </span>
      ),
    }),
    memberColumn.accessor("is_registered", {
      header: t("Ledger Status"),
      cell: ({ row }) =>
        row.original.is_registered ? (
          <Badge bg="success" className="d-inline-flex align-items-center gap-1">
            <CheckCircle2 size={12} />
            {t("Registered")}
          </Badge>
        ) : (
          <Badge bg="secondary" className="d-inline-flex align-items-center gap-1">
            <XCircle size={12} />
            {t("Not in Ledger")}
          </Badge>
        ),
    }),
  ] as ColumnDef<AltSchema, unknown>[];

  return (
    <main>
      <BaseSectionHeader name={data ? `${title} - ${data.owner.character_name}` : title}>
        <div className="d-flex align-items-center gap-2 flex-wrap">
          {data?.last_sync ? (
            <div
              className="d-flex align-items-center gap-1 text-muted small me-2"
              title={formatDate(data.last_sync)}
            >
              <Clock size={14} />
              <span>{t("Last Sync")}:</span>
              <strong className="text-light">
                {formatRelativeTime(data.last_sync)}
              </strong>
            </div>
          ) : onUpdate && data ? (
            <div className="d-flex align-items-center gap-1 text-muted small me-2">
              <Clock size={14} />
              <span>{t("Last Sync")}:</span>
              <strong className="text-light">{t("Never")}</strong>
            </div>
          ) : null}
          {onUpdate && (
            <Button
              className="aa-btn aa-btn-primary d-inline-flex align-items-center gap-1"
              disabled={
                update.isPending ||
                cooldown > 0 ||
                (data ? !data.can_update && cooldown === 0 : false)
              }
              onClick={() => update.mutate()}
              aria-label={t("Update")}
            >
              {update.isPending ? (
                <Spinner animation="border" size="sm" role="status" aria-hidden="true" />
              ) : (
                <RotateCw size={14} />
              )}
              <span>
                {update.isPending
                  ? t("Updating...")
                  : cooldown > 0
                    ? `${t("Update")} (${formatCooldown(cooldown)})`
                    : t("Update")}
              </span>
            </Button>
          )}
          {headerAction}
        </div>
      </BaseSectionHeader>
      <section className="mt-3 d-flex flex-column gap-3">
        {isLoading && <FetchingLoader message={t("Loading...")} />}
        {error && <ErrorLoader title={t("Error")} message={error.message} />}
        {message && (
          <Alert variant={message.variant} onClose={() => setMessage(null)} dismissible>
            {message.text}
          </Alert>
        )}

        {data && (
          <>
            <Row className="g-2" aria-label={t("Statistics")}>
              {[
                { label: t("Total"), value: data.dashboard.auth_count, icon: Users, color: "#60a5fa" },
                { label: t("Registered"), value: data.dashboard.active_count, icon: UserCheck, color: "#34d399" },
                ...(data.dashboard.inactive_count !== null &&
                  data.dashboard.inactive_count !== undefined
                  ? [{ label: t("Inactive"), value: data.dashboard.inactive_count, icon: UserMinus, color: "#fbbf24" }]
                  : []),
                { label: t("Missing"), value: data.dashboard.missing_count, icon: UserX, color: "#fb7185" },
              ].map((item) => {
                const Icon = item.icon;
                return (
                  <Col key={item.label} xs={6} md>
                    <div className="aa-panel lg-stat-card">
                      <div className="lg-stat-header">
                        <span className="lg-stat-label">{item.label}</span>
                        <Icon className="lg-stat-icon" color={item.color} size={24} />
                      </div>
                      <span className="lg-stat-value">{item.value}</span>
                    </div>
                  </Col>
                );
              })}
            </Row>

            {(data.dashboard.issues ?? []).length > 0 && (
              <Alert variant="warning">
                {t("Please re-register characters with issues")}:{" "}
                {(data.dashboard.issues ?? []).join(", ")}
              </Alert>
            )}

            <div className="lg-entries-grid">
              {data.registered.map((entry) => {
                const normStatus = entry.status?.toLowerCase();
                const isError = normStatus === "error" || Boolean(data.dashboard.issues?.includes(entry.name));
                const isTokenError = normStatus === "token_error";
                const isOk = normStatus === "ok";
                const hasProblem = isError || isTokenError;

                const cardClass = isError
                  ? "lg-entry-error"
                  : isTokenError
                    ? "lg-entry-warning"
                    : "";

                let badgeClass = "lg-badge-secondary";
                let StatusIcon = AlertCircle;
                let statusLabel = entry.status ?? t("Unknown");

                if (isOk) {
                  badgeClass = "lg-badge-ok";
                  StatusIcon = CheckCircle2;
                  statusLabel = t("OK");
                } else if (isError) {
                  badgeClass = "lg-badge-error";
                  StatusIcon = AlertCircle;
                  statusLabel = t("Error");
                } else if (isTokenError) {
                  badgeClass = "lg-badge-token-error";
                  StatusIcon = AlertTriangle;
                  statusLabel = t("Token Error");
                }

                return (
                  <div
                    key={entry.owner_id}
                    className={`aa-panel lg-entry ${cardClass}`}
                  >
                    <div className="lg-entry-header">
                      {entry.icon && (
                        <img
                          src={entry.icon}
                          alt={entry.name}
                          className="lg-entry-icon"
                        />
                      )}
                      <div className="lg-entry-info">
                        <h4 className="lg-entry-name">{entry.name}</h4>
                      </div>
                    </div>

                    {entry.error_message && (
                      <div className="lg-error-banner" role="alert">
                        {entry.error_message}
                      </div>
                    )}

                    {entry.sections && entry.sections.length > 0 && (
                      <div className="lg-sections-list">
                        {entry.sections.map((sec) => {
                          let dotClass = "lg-dot-muted";
                          if (sec.is_success === true) dotClass = "lg-dot-ok";
                          else if (sec.is_success === false) dotClass = "lg-dot-error";
                          else if (sec.has_token_error) dotClass = "lg-dot-warning";

                          return (
                            <div key={sec.section} className="lg-section-item">
                              <span className="d-inline-flex align-items-center gap-2">
                                <span
                                  className={`lg-section-dot ${dotClass}`}
                                  aria-hidden="true"
                                />
                                <span>{sec.section_name}</span>
                              </span>
                              <span>
                                {sec.has_token_error
                                  ? t("Token Error")
                                  : sec.is_success === true
                                    ? t("OK")
                                    : sec.is_success === false
                                      ? t("Failed")
                                      : t("Pending")}
                              </span>
                            </div>
                          );
                        })}
                      </div>
                    )}

                    <div className="lg-entry-badge-row">
                      {entry.status && (
                        <span className={`lg-status-badge ${badgeClass}`}>
                          {hasProblem && (
                            <span className="aa-pending-dot-container me-1" aria-hidden="true">
                              <span
                                className={
                                  isError
                                    ? "aa-danger-dot-ping"
                                    : "aa-pending-dot-ping"
                                }
                              />
                              <span
                                className={
                                  isError
                                    ? "aa-danger-dot-core"
                                    : "aa-pending-dot-core"
                                }
                              />
                            </span>
                          )}
                          <StatusIcon size={12} aria-hidden="true" />
                          <span>{statusLabel}</span>
                        </span>
                      )}

                      {entry.last_sync !== undefined && (
                        <span
                          className="lg-entry-last-sync"
                          title={entry.last_sync ? formatDate(entry.last_sync) : undefined}
                        >
                          <Clock size={12} aria-hidden="true" />
                          <span>{entry.last_sync ? formatRelativeTime(entry.last_sync) : t("Never")}</span>
                        </span>
                      )}
                    </div>

                    {(showCardLedger || onDelete) && (
                      <div className="lg-entry-actions">
                        {showCardLedger &&
                          renderTooltip(
                            t("View Ledger"),
                            <Link
                              className="aa-btn aa-btn-success aa-btn-sm"
                              to={ledgerPath(entry.owner_id)}
                              aria-label={t("View Ledger")}
                            >
                              <LogIn size={14} />
                            </Link>,
                          )}
                        {onDelete &&
                          renderTooltip(
                            t("Delete"),
                            <button
                              type="button"
                              className="aa-btn aa-btn-danger aa-btn-sm"
                              aria-label={t("Delete")}
                              onClick={() => setPending(entry)}
                            >
                              <Trash2 size={14} />
                            </button>,
                          )}
                      </div>
                    )}
                  </div>
                );
              })}

              {data.missing.map((entry) => (
                <div
                  key={entry.owner_id}
                  className="aa-panel lg-entry lg-entry-missing"
                >
                  <div className="lg-entry-header">
                    {entry.icon && (
                      <img
                        src={entry.icon}
                        alt={entry.name}
                        className="lg-entry-icon"
                      />
                    )}
                    <div className="lg-entry-info">
                      <h4 className="lg-entry-name">{entry.name}</h4>
                    </div>
                  </div>
                  <div className="small text-muted">
                    {t("{{entry}} is not registered in Ledger.", { entry: missingLabel ?? entryLabel })}
                  </div>
                </div>
              ))}
              {data.registered.length === 0 && data.missing.length === 0 && (
                <Alert variant="info">{t("Nothing to show")}</Alert>
              )}
            </div>

            {data.members.length > 0 && (
              <BaseTable
                columns={memberColumns}
                data={data.members}
                emptyText={t("No Characters found.")}
                exportFileName="members.csv"
              />
            )}
          </>
        )}
      </section>

      <BaseModal
        title={t("Delete {{entry}}", { entry: pending?.name ?? entryLabel })}
        show={pending !== null}
        onHide={() => setPending(null)}
        size={ModalSize.medium}
        footer={
          <>
            <Button variant="secondary" onClick={() => setPending(null)}>
              {t("Cancel")}
            </Button>
            <Button
              variant="danger"
              disabled={remove.isPending}
              onClick={() => pending && remove.mutate(pending.owner_id)}
            >
              {t("Delete")}
            </Button>
          </>
        }
      >
        {t("Are you sure you want to delete this entry?")}
      </BaseModal>
    </main>
  );
}

export default AdministrationView;
