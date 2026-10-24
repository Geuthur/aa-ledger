// React
import type React from "react";

// Third Party
import { BellOff } from "lucide-react";
import { Card } from "react-bootstrap";
import { useTranslation } from "react-i18next";

// Styles
import styles from "@/Styles/modules/SettingsPage.module.css";

export interface BaseUserSettingsCardProps {
  appName?: string;
  disableNotifications: boolean;
  isPending: boolean;
  isError: boolean;
  onToggleNotifications: (checked: boolean) => void;
  title?: string;
  description?: string;
}

export const BaseUserSettingsCard: React.FC<BaseUserSettingsCardProps> = ({
  appName = "Alliance Auth",
  disableNotifications,
  isPending,
  isError,
  onToggleNotifications,
  title,
  description,
}) => {
  const { t } = useTranslation();

  return (
    <Card className="bg-dark text-light border-0 shadow-sm mb-4">
      <Card.Body className={styles["setting-row"]}>
        <div className={styles["setting-copy"]}>
          <div className={styles["setting-title"]}>
            <BellOff size={18} aria-hidden="true" />
            <label htmlFor="disable-notifications">
              {title ?? t("Disable all notifications")}
            </label>
          </div>
          <p className={styles["setting-description"]}>
            {description ??
              t(
                "When enabled, {{app}} will not send notifications to your Alliance Auth or Discord account.",
                { app: appName },
              )}
          </p>
          {isError && (
            <p className={styles["error-message"]} role="alert">
              {t("Could not save this setting. Your previous preference was restored.")}
            </p>
          )}
          {isPending && (
            <p className={styles["save-status"]} role="status">
              {t("Saving…")}
            </p>
          )}
        </div>
        <input
          id="disable-notifications"
          className={styles["switch"]}
          type="checkbox"
          role="switch"
          checked={disableNotifications}
          disabled={isPending}
          onChange={(event) => onToggleNotifications(event.currentTarget.checked)}
        />
      </Card.Body>
    </Card>
  );
};

export default BaseUserSettingsCard;
