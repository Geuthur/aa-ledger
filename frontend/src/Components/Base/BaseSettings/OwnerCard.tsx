// Third Party
import {
  AlertCircle,
  AlertTriangle,
  Building2,
  CheckCircle2,
  Clock,
  RotateCw,
  Shield,
  Trash2,
  User,
} from "lucide-react";
import { Button } from "react-bootstrap";
import { useTranslation } from "react-i18next";

// Styles
// AA Base
import styles from "@/Components/Base/BaseSettings/Settings.module.css";

import type { BaseOwner, BaseOwnerCardProps } from "@/Components/Base/BaseSettings/types";

/** Card of a registered owner: status badge, update sections and action buttons. */
export function BaseOwnerCard<T extends BaseOwner = BaseOwner>({
  owner,
  isUpdating = false,
  cooldown = 0,
  onTriggerUpdate,
  onDeleteClick,
  renderCustomContent,
  renderActions,
}: BaseOwnerCardProps<T>) {
  const { t } = useTranslation();

  const status = (owner.status || "incomplete").toLowerCase();
  const isError = status === "error";
  const isTokenError = status === "token_error";
  const cardClass = isError
    ? styles["char-card-warning"]
    : isTokenError
      ? styles["char-card-error"]
      : "";

  const renderStatusBadge = () => {
    let badgeClass = styles["badge-incomplete"];
    let label = t("Incomplete");
    let Icon = AlertTriangle;

    if (status === "ok") {
      badgeClass = styles["badge-ok"];
      label = t("OK");
      Icon = CheckCircle2;
    } else if (isError) {
      badgeClass = styles["badge-error"];
      label = t("Error");
      Icon = AlertTriangle;
    } else if (isTokenError) {
      badgeClass = styles["badge-token-error"];
      label = t("Token Error");
      Icon = AlertCircle;
    } else if (status === "disabled") {
      badgeClass = styles["badge-disabled"];
      label = t("Disabled");
      Icon = AlertCircle;
    }

    return (
      <span className={`${styles["status-badge"]} ${badgeClass}`}>
        {(isError || isTokenError) && (
          <span className="aa-pending-dot-container me-1" aria-hidden="true">
            <span className={isTokenError ? "aa-danger-dot-ping" : "aa-pending-dot-ping"} />
            <span className={isTokenError ? "aa-danger-dot-core" : "aa-pending-dot-core"} />
          </span>
        )}
        <Icon size={12} aria-hidden="true" />
        <span>{label}</span>
      </span>
    );
  };

  const type = (owner.owner_type ?? "").toLowerCase();
  const TypeIcon = type === "corporation" ? Building2 : type === "alliance" ? Shield : User;
  const typeLabel =
    type === "corporation" ? t("Corporation") : type === "alliance" ? t("Alliance") : t("Character");
  const typeBadgeClass =
    type === "corporation"
      ? "bg-primary text-white border-black"
      : type === "alliance"
        ? "bg-success text-white border-black"
        : "bg-info text-white border-black";

  return (
    <article className={`${styles["char-card"]} ${cardClass}`}>
      <div className={styles["char-header"]}>
        {owner.avatar_url ? (
          <img
            src={owner.avatar_url}
            alt={owner.name}
            className={`${styles["portrait"]} ${type === "corporation" ? styles["portrait-corp"] : ""}`}
          />
        ) : (
          <div
            className={`${styles["portrait"]} d-flex align-items-center justify-content-center bg-dark text-light`}
          >
            <TypeIcon size={24} />
          </div>
        )}
        <div className={styles["char-info"]}>
          <div className="d-flex align-items-center justify-content-between gap-2">
            <h3 className={styles["char-name"]} title={owner.name}>
              {owner.name}
            </h3>
            <span
              className={`badge border d-inline-flex align-items-center gap-1 flex-shrink-0 ${typeBadgeClass}`}
            >
              <TypeIcon size={11} />
              {typeLabel}
            </span>
          </div>
          {owner.subtitle && <p className={styles["char-corp"]}>{owner.subtitle}</p>}
        </div>
      </div>

      {owner.error_message && (
        <div className={styles["error-banner"]} role="alert">
          {owner.error_message}
        </div>
      )}

      {owner.sections && owner.sections.length > 0 && (
        <div className={styles["sections-list"]}>
          {owner.sections.map((sec) => {
            let dotClass = styles["dot-muted"];
            if (sec.is_success === true) dotClass = styles["dot-ok"];
            if (sec.is_success === false) dotClass = styles["dot-warning"];
            if (sec.has_token_error) dotClass = styles["dot-error"];

            return (
              <div key={sec.section} className={styles["section-item"]}>
                <span className="d-inline-flex align-items-center gap-2">
                  <span className={`${styles["section-dot"]} ${dotClass}`} aria-hidden="true" />
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

      {renderCustomContent?.(owner)}

      <div className={styles["badge-row"]}>
        {renderStatusBadge()}
        <span
          className={styles["last-sync"]}
          title={owner.last_sync ? `${t("Last sync")}: ${owner.last_sync}` : undefined}
        >
          <Clock size={12} aria-hidden="true" />
          <span>{owner.last_sync ? owner.last_sync.slice(5) : t("Never")}</span>
        </span>
      </div>

      {(onTriggerUpdate || onDeleteClick || renderActions) && (
        <div className="d-flex align-items-center justify-content-between gap-2 mt-2 pt-2 border-top border-secondary flex-wrap">
          <div>{renderActions?.(owner)}</div>
          <div className="d-flex align-items-center gap-2 ms-auto">
            {onTriggerUpdate && (
              <Button
                variant="secondary"
                size="sm"
                className="d-flex align-items-center gap-1"
                disabled={isUpdating || cooldown > 0}
                onClick={() => onTriggerUpdate(owner.id)}
                aria-label={t("Update Owner")}
              >
                {isUpdating ? (
                  <span className="spinner-border spinner-border-sm" />
                ) : (
                  <RotateCw size={13} />
                )}
                <span>{cooldown > 0 ? `${cooldown}s` : t("Update")}</span>
              </Button>
            )}
            {onDeleteClick && (
              <Button
                variant="danger"
                size="sm"
                className="d-flex align-items-center gap-1"
                onClick={() => onDeleteClick(owner)}
                aria-label={t("Delete Owner")}
              >
                <Trash2 size={13} />
                <span>{t("Delete")}</span>
              </Button>
            )}
          </div>
        </div>
      )}
    </article>
  );
}
