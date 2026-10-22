// React
import React from "react";

// Third Party
import { AlertCircle, Plus, User } from "lucide-react";
import { Button } from "react-bootstrap";
import { useTranslation } from "react-i18next";

// Styles
// AA Base
import styles from "@/Components/Base/BaseSettings/Settings.module.css";

import type { BaseMissingOwner, MissingOwnerCardProps } from "@/Components/Base/BaseSettings/types";

/** Card for an entity (e.g. an alt) that belongs to the user but is not registered in the app. */
export const MissingOwnerCard: React.FC<MissingOwnerCardProps<BaseMissingOwner>> = ({
  missing,
  appName = "Alliance Auth",
  actionUrl,
  actionLabel,
}) => {
  const { t } = useTranslation();

  return (
    <article className={`${styles["char-card"]} ${styles["missing-card"]} opacity-50`}>
      <div className={styles["char-header"]}>
        {missing.avatar_url ? (
          <img src={missing.avatar_url} alt={missing.name} className={styles["portrait"]} />
        ) : (
          <div
            className={`${styles["portrait"]} d-flex align-items-center justify-content-center bg-secondary text-light`}
          >
            <User size={24} />
          </div>
        )}
        <div className={styles["char-info"]}>
          <div className="d-flex align-items-center justify-content-between gap-2">
            <h3 className={styles["char-name"]}>{missing.name}</h3>
            <span className={`${styles["status-badge"]} ${styles["missing-badge"]}`}>
              <AlertCircle size={11} aria-hidden="true" />
              <span>{t("Not Registered")}</span>
            </span>
          </div>
          {missing.subtitle && <p className={styles["char-corp"]}>{missing.subtitle}</p>}
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
