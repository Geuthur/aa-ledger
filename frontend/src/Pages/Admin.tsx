// React
import { useState } from "react";

// Third Party
import { useMutation } from "@tanstack/react-query";
import { Alert, Form } from "react-bootstrap";
import { useTranslation } from "react-i18next";

import { queueUpdate } from "@/Api/ApiCalls";
import type { AdminUpdateRequest } from "@/Api/schema";
import BaseSectionHeader from "@/Components/Base/BaseHeader";

type Target = AdminUpdateRequest["target"];

interface UpdateFormProps {
  target: Target;
  title: string;
  idLabel: string;
  forceRefresh: boolean;
  onQueued: (message: string) => void;
  onFailed: (message: string) => void;
}

function UpdateForm({ target, title, idLabel, forceRefresh, onQueued, onFailed }: UpdateFormProps) {
  const { t } = useTranslation();
  const [eveId, setEveId] = useState("");

  const mutation = useMutation({
    mutationFn: (request: AdminUpdateRequest) => queueUpdate(request),
    onSuccess: (data) => onQueued(data.message),
    onError: (error: Error) => onFailed(error.message),
  });

  return (
    <Form
      className="aa-panel d-flex flex-column gap-2"
      onSubmit={(event) => {
        event.preventDefault();
        mutation.mutate({
          target,
          eve_id: eveId ? Number(eveId) : null,
          force_refresh: forceRefresh,
        });
      }}
    >
      <h5>{title}</h5>
      <Form.Group controlId={`${target}-id`}>
        <Form.Label>{idLabel}</Form.Label>
        <Form.Control
          type="number"
          min={1}
          value={eveId}
          onChange={(event) => setEveId(event.target.value)}
        />
        <Form.Text muted>{t("Leave empty to update all")}</Form.Text>
      </Form.Group>
      <button type="submit" className="aa-btn aa-btn-primary align-self-start" disabled={mutation.isPending}>
        {t("Queue Update")}
      </button>
    </Form>
  );
}

function Admin() {
  const { t } = useTranslation();
  const [forceRefresh, setForceRefresh] = useState(false);
  const [message, setMessage] = useState<{ variant: "success" | "danger"; text: string } | null>(
    null,
  );

  return (
    <main>
      <BaseSectionHeader name={t("Administration")} />
      <section className="mt-3 d-flex flex-column gap-3">
        {message && (
          <Alert variant={message.variant} onClose={() => setMessage(null)} dismissible>
            {message.text}
          </Alert>
        )}
        <Form.Check
          type="switch"
          id="force-refresh"
          label={t("Mark all tasks as Force Refresh")}
          checked={forceRefresh}
          onChange={(event) => setForceRefresh(event.target.checked)}
        />
        <div className="row g-3">
          <div className="col-12 col-lg-6">
            <UpdateForm
              target="characters"
              title={t("Update Characters")}
              idLabel={t("Character ID (optional)")}
              forceRefresh={forceRefresh}
              onQueued={(text) => setMessage({ variant: "success", text })}
              onFailed={(text) => setMessage({ variant: "danger", text })}
            />
          </div>
          <div className="col-12 col-lg-6">
            <UpdateForm
              target="corporations"
              title={t("Update Corporations")}
              idLabel={t("Corporation ID (optional)")}
              forceRefresh={forceRefresh}
              onQueued={(text) => setMessage({ variant: "success", text })}
              onFailed={(text) => setMessage({ variant: "danger", text })}
            />
          </div>
        </div>
      </section>
    </main>
  );
}

export default Admin;
