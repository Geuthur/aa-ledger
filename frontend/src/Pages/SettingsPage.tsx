// React
import React, { useState } from "react";
import { Link } from "react-router-dom";

// Third Party
import { BookOpen, Settings2, UserRoundX, Users } from "lucide-react";
import { Button, Card } from "react-bootstrap";
import { useTranslation } from "react-i18next";

// Styles
import styles from "@/Styles/modules/SettingsPage.module.css";

// API
import type { SettingsMissingOwnerSchema, SettingsOwnerSchema } from "@/Api/schema";
import {
    BaseOwnerSettingsSection,
    UnregisteredModal,
    BaseUserSettingsCard,
    useUnregistered,
} from "@/Components/Base/BaseSettings";
import {
    useSettingsOwnerActions,
    useSettingsOwners,
    useUserSettings,
} from "@/Components/Settings/Hooks";

export const SettingsPage: React.FC = () => {
    const { t } = useTranslation();

    const [unregisteredOwner, setUnregisteredOwner] = useState<SettingsOwnerSchema | null>(null);

    const { data, isLoading, isError, updateMutation } = useUserSettings();
    const {
        data: ownersData,
        isLoading: isLoadingOwners,
        isError: isErrorOwners,
    } = useSettingsOwners();
    const {
        data: unregisteredData,
        isLoading: isLoadingUnregistered,
        isError: isErrorUnregistered,
    } = useUnregistered(unregisteredOwner?.owner_type ?? null, unregisteredOwner?.id ?? null);
    const actions = useSettingsOwnerActions(
        ownersData?.registered,
        ownersData?.cooldown_seconds ?? 0,
    );

    if (isLoading) {
        return (
            <div className="aa-loader-container">
                <span className="spinner-border" />
                <span>{t("Loading settings…")}</span>
            </div>
        );
    }

    if (isError || !data) {
        return (
            <Card className="bg-dark text-light border-0 shadow-sm" role="alert">
                <Card.Body className={styles["error"]}>
                    {t("Failed to load settings. Please try refreshing the page.")}
                </Card.Body>
            </Card>
        );
    }

    return (
        <Card className={`${styles["page"]} mx-auto border-0`}>
            <Card.Body className="bg-dark-body">
                {/* Page Header */}
                <Card.Header className="d-flex align-items-center gap-3 mb-4 bg-dark">
                    <Settings2 size={24} aria-hidden="true" color="royalblue" />
                    <div>
                        <h1 className={`${styles["title"]} fs-4 fw-bold m-0`}>{t("Settings")}</h1>
                        <p className={`${styles["description"]} small mt-1 mb-0`}>
                            {t("Manage your Ledger preferences.")}
                        </p>
                    </div>
                </Card.Header>

                {/* User Notifications Card */}
                <BaseUserSettingsCard
                    appName="Ledger"
                    disableNotifications={data.disable_notifications}
                    isPending={updateMutation.isPending}
                    isError={updateMutation.isError}
                    onToggleNotifications={(checked) =>
                        updateMutation.mutate({ disable_notifications: checked })
                    }
                />

                {/* Character & Corporation Status Section */}
                <BaseOwnerSettingsSection<SettingsOwnerSchema, SettingsMissingOwnerSchema>
                    title={t("Owner Status")}
                    description={t("ESI synchronization status of your linked owners.")}
                    icon={<Users size={20} aria-hidden="true" color="royalblue" />}
                    appName="Ledger"
                    owners={ownersData?.registered ?? []}
                    missingOwners={ownersData?.missing ?? []}
                    isLoading={isLoadingOwners}
                    isError={isErrorOwners}
                    errorMessage={t("Failed to load owner status.")}
                    emptyMessage={t("No owners found.")}
                    globalCooldown={actions.globalCooldown}
                    isUpdatingAll={actions.isUpdatingAll}
                    onUpdateAll={actions.updateAll}
                    feedbackMessage={actions.feedback}
                    onDismissFeedback={actions.clearFeedback}
                    onTriggerSingleUpdate={actions.updateOwner}
                    updatingOwnerId={actions.updatingOwnerId}
                    ownerCooldowns={actions.ownerCooldowns}
                    onDeleteOwner={actions.deleteOwner}
                    isDeleting={actions.isDeleting}
                    deleteModalTitle={t("Delete Owner")}
                    deleteModalDescription={() =>
                        t(
                            "This will remove this owner from Ledger along with all associated wallets, transactions, and audit records. This action cannot be undone.",
                        )
                    }
                    missingActionUrl="/ledger/character/add/"
                    missingActionLabel={t("Add to {{app}}", { app: "Ledger" })}
                    isUpdatable={(owner) => owner.owner_type !== "alliance"}
                    isDeletable={(owner) => owner.owner_type !== "alliance"}
                    renderCardActions={(owner) => (
                        <>
                            <div className="d-flex align-items-center gap-2 ms-auto">
                                <Link
                                    className="btn btn-sm btn-secondary d-flex align-items-center gap-1"
                                    to={`/ledger/${owner.owner_type}/${owner.id}/`}
                                >
                                    <BookOpen size={14} />
                                    <span>{t("View Ledger")}</span>
                                </Link>
                                {(owner.owner_type === "corporation" || owner.owner_type === "alliance") && (
                                    <Button
                                        variant="secondary"
                                        size="sm"
                                        className="d-flex align-items-center gap-1"
                                        onClick={() => setUnregisteredOwner(owner)}
                                    >
                                        <UserRoundX size={14} />
                                        <span>{t("Unregistered")}</span>
                                    </Button>
                                )}
                            </div>
                        </>
                    )}
                />

                <UnregisteredModal
                    show={!!unregisteredOwner}
                    onHide={() => setUnregisteredOwner(null)}
                    title={
                        unregisteredOwner?.owner_type === "alliance"
                            ? t("Unregistered corporations of {{name}}", { name: unregisteredOwner.name })
                            : t("Unregistered members of {{name}}", { name: unregisteredOwner?.name ?? "" })
                    }
                    description={
                        unregisteredOwner?.owner_type === "alliance"
                            ? t("Corporations of this alliance that are not registered in Ledger.")
                            : t("Characters of this corporation that are not registered in Ledger.")
                    }
                    items={unregisteredData?.items ?? []}
                    isLoading={isLoadingUnregistered}
                    isError={isErrorUnregistered}
                    errorMessage={t("Failed to load unregistered entries.")}
                    emptyMessage={t("Everything is registered.")}
                />
            </Card.Body>
        </Card>
    );
};

export default SettingsPage;
