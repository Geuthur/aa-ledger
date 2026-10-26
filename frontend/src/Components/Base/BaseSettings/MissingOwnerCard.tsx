// React
import React from "react";

// Third Party
import { AlertCircle, Plus } from "lucide-react";
import { Button } from "react-bootstrap";
import { useTranslation } from "react-i18next";

// Styles
import styles from "@/Components/Base/BaseSettings/Settings.module.css";

import type { BaseMissingOwner, MissingOwnerCardProps } from "@/Components/Base/BaseSettings/types";
// AA Base
import { OwnerPortrait } from "@/Components/Base/OwnerPortrait";

/** Card for an entity (e.g. an alt) that belongs to the user but is not registered in the app. */
export const MissingOwnerCard: React.FC<MissingOwnerCardProps<BaseMissingOwner>> = ({
  missing,
  appName = "Alliance Auth",
  actionUrl,
  actionLabel,
}) => {
  const { t } = useTranslation();

  return (
    <article className={`${styles["char-card"]} ${styles["missing-card"]} d-flex flex-column gap-3 p-3 opacity-50`}>
      <div className="d-flex align-items-center gap-3">
        <OwnerPortrait src={missing.avatar_url} alt={missing.name} bordered />
        <div className={`${styles["char-info"]} flex-grow-1`}>
          <div className="d-flex align-items-center justify-content-between gap-2">
            <h3 className={`${styles["char-name"]} m-0 fs-6 fw-semibold text-truncate`}>{missing.name}</h3>
            <span className={`${styles["status-badge"]} d-inline-flex align-items-center gap-1 px-2 py-1 fw-semibold text-capitalize ${styles["missing-badge"]}`}>
              <AlertCircle size={11} aria-hidden="true" />
              <span>{t("Not Registered")}</span>
            </span>
          </div>
          {missing.subtitle && <p className={`${styles["char-corp"]} m-0 text-truncate`}>{missing.subtitle}</p>}
        </div>
      </div>

      <p className="small text-muted mb-0">
        {t("{{name}} is not registered in {{app}}.", { name: missing.name, app: appName })}
      </p>

      {actionUrl && (
        <div className="d-flex justify-content-end mt-auto pt-2 border-top border-secondary">
          <Button
            href={actionUrl}
            variant="primary"
            size="sm"
            className="d-flex align-items-center gap-1"
          >
            <Plus size={13} />
            <span>{actionLabel ?? t("Add to {{app}}", { app: appName })}</span>
          </Button>
        </div>
      )}
    </article>
  );
};
