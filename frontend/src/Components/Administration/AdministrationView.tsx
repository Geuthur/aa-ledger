// React
import { useState } from "react";
import { Link } from "react-router";

// Third Party
import { useMutation, useQueryClient } from "@tanstack/react-query";
import type { QueryKey } from "@tanstack/react-query";
import { createColumnHelper } from "@tanstack/react-table";
import type { ColumnDef } from "@tanstack/react-table";
import { LogIn, Trash2, UserCheck, UserMinus, UserX, Users } from "lucide-react";
import { Alert, Button, Col, Modal, Row } from "react-bootstrap";
import { useTranslation } from "react-i18next";

import type { AdminOwnerSchema, AdministrationResponse, AltSchema, MessageSchema } from "@/Api/schema";
import ErrorLoader from "@/Components/Loader/ErrorLoader";
import FetchingLoader from "@/Components/Loader/FetchingLoader";
import BaseSectionHeader from "@/Components/Sections/BaseHeader";
import { BaseTable } from "@/Components/Tables/BaseTable";
import { renderTooltip } from "@/Components/Tables/BaseTable/tableHelper";

const memberColumn = createColumnHelper<AltSchema>();

export interface AdministrationViewProps {
  title: string;
  data?: AdministrationResponse;
  isLoading: boolean;
  error: Error | null;
  /** Singular label of the registered entries, e.g. "Character". */
  entryLabel: string;
  queryKey: QueryKey;
  /** Route of the ledger of an entry. */
  ledgerPath: (ownerId: number) => string;
  /** Removes an entry; omit if entries cannot be removed on this page. */
  onDelete?: (ownerId: number) => Promise<MessageSchema>;
}

function AdministrationView({
  title,
  data,
  isLoading,
  error,
  entryLabel,
  queryKey,
  ledgerPath,
  onDelete,
}: AdministrationViewProps) {
  const { t } = useTranslation();
  const queryClient = useQueryClient();
  const [pending, setPending] = useState<AdminOwnerSchema | null>(null);
  const [message, setMessage] = useState<{ variant: "success" | "danger"; text: string } | null>(
    null,
  );

  const remove = useMutation({
    mutationFn: (ownerId: number) => (onDelete ? onDelete(ownerId) : Promise.reject()),
    onSuccess: (result) => {
      setMessage({ variant: "success", text: result.message });
      return queryClient.invalidateQueries({ queryKey });
    },
    onError: (failure: Error) => setMessage({ variant: "danger", text: failure.message }),
    onSettled: () => setPending(null),
  });

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
  ] as ColumnDef<AltSchema, unknown>[];

  return (
    <main>
      <BaseSectionHeader name={data ? `${title} - ${data.owner.character_name}` : title} />
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

            <div className="d-flex flex-wrap gap-3">
              {data.registered.map((entry) => (
                <div
                  key={entry.owner_id}
                  className="aa-panel lg-entry d-flex flex-column align-items-center gap-2"
                >
                  <div className="fw-bold">
                    {entry.name}{" "}
                    {entry.status && <span className="badge bg-secondary">{entry.status}</span>}
                  </div>
                  <img src={entry.icon ?? ""} alt="" width={96} height={96} className="rounded" />
                  <div className="d-flex justify-content-center gap-2">
                    {renderTooltip(
                      t("View Ledger"),
                      <Link
                        className="lg-btn lg-btn-success lg-btn-sm"
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
                          className="lg-btn lg-btn-danger lg-btn-sm"
                          aria-label={t("Delete")}
                          onClick={() => setPending(entry)}
                        >
                          <Trash2 size={14} />
                        </button>,
                      )}
                  </div>
                </div>
              ))}
              {data.missing.map((entry) => (
                <div
                  key={entry.owner_id}
                  className="aa-panel lg-entry lg-entry-missing d-flex flex-column align-items-center gap-2"
                >
                  <div className="fw-bold">{entry.name}</div>
                  <img src={entry.icon ?? ""} alt="" width={96} height={96} className="rounded" />
                  <div className="small">
                    {t("{{entry}} is not registered in Ledger.", { entry: entryLabel })}
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

      <Modal show={pending !== null} onHide={() => setPending(null)} centered restoreFocus={false}>
        <Modal.Header closeButton>
          <Modal.Title>{t("Delete {{entry}}", { entry: pending?.name ?? entryLabel })}</Modal.Title>
        </Modal.Header>
        <Modal.Body>{t("Are you sure you want to delete this entry?")}</Modal.Body>
        <Modal.Footer>
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
        </Modal.Footer>
      </Modal>
    </main>
  );
}

export default AdministrationView;
