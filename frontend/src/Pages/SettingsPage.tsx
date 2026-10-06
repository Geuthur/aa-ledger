// React
import React from "react";

// Third Party
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { BellOff, Settings2 } from "lucide-react";
import { useTranslation } from "react-i18next";

// Styles
import styles from "@/Styles/modules/SettingsPage.module.css";

import { loadUserSettings, updateUserSettings } from "@/Api/ApiCalls";
import { queryKeys } from "@/Api/query";
import type { UserSettingsSchema } from "@/Api/schema";

export const SettingsPage: React.FC = () => {
  const { t } = useTranslation();
  const queryClient = useQueryClient();
  const { data, isLoading, isError } = useQuery({
    queryKey: queryKeys.UserSettings,
    queryFn: loadUserSettings,
  });

  const updateMutation = useMutation({
    mutationFn: updateUserSettings,
    onMutate: async (settings) => {
      await queryClient.cancelQueries({ queryKey: queryKeys.UserSettings });
      const previous = queryClient.getQueryData<UserSettingsSchema>(queryKeys.UserSettings);
      queryClient.setQueryData<UserSettingsSchema>(queryKeys.UserSettings, settings);
      return { previous };
    },
    onError: (_error, _settings, context) => {
      if (context?.previous) {
        queryClient.setQueryData(queryKeys.UserSettings, context.previous);
      }
    },
    onSuccess: (settings) => {
      queryClient.setQueryData(queryKeys.UserSettings, settings);
    },
  });

  if (isLoading) {
    return (
      <div className="aa-loader-container">
        <span className="spinner-border" />
        <span>{t("Loading settings...")}</span>
      </div>
    );
  }

  if (isError || !data) {
    return (
      <div className={`aa-panel ${styles["error"]}`} role="alert">
        {t("Failed to load settings. Please try refreshing the page.")}
      </div>
    );
  }

  return (
    <main className={`aa-panel-light ${styles["page"]}`}>
      <header className={styles["header"]}>
        <Settings2 size={24} aria-hidden="true" />
        <div>
          <h1 className={styles["title"]}>{t("Settings")}</h1>
          <p className={styles["description"]}>{t("Manage your Ledger preferences.")}</p>
        </div>
      </header>

      <section className={`aa-panel ${styles["setting-row"]}`}>
        <div className={styles["setting-copy"]}>
          <div className={styles["setting-title"]}>
            <BellOff size={18} aria-hidden="true" />
            <label htmlFor="disable-notifications">{t("Disable all notifications")}</label>
          </div>
          <p className={styles["setting-description"]}>
            {t("When enabled, Ledger will not send notifications to your Alliance Auth or Discord account.")}
          </p>
          {updateMutation.isError && (
            <p className={styles["error-message"]} role="alert">
              {t("Could not save this setting. Your previous preference was restored.")}
            </p>
          )}
          {updateMutation.isPending && (
            <p className={styles["save-status"]} role="status">{t("Saving...")}</p>
          )}
        </div>
        <input
          id="disable-notifications"
          className={styles["switch"]}
          type="checkbox"
          role="switch"
          checked={data.disable_notifications}
          disabled={updateMutation.isPending}
          onChange={(event) =>
            updateMutation.mutate({ disable_notifications: event.currentTarget.checked })
          }
        />
      </section>
    </main>
  );
};

export default SettingsPage;
