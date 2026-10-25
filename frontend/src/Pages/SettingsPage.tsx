// React
import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";

// Third Party
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { BookOpen, Settings2, UserRoundX, Users } from "lucide-react";
import { Button, Card } from "react-bootstrap";
import { useTranslation } from "react-i18next";

// Styles
import styles from "@/Styles/modules/SettingsPage.module.css";

// API
import {
    deleteSettingsOwner,
    loadSettingsOwners,
    loadSettingsUnregistered,
    loadUserSettings,
    triggerSettingsOwnerUpdate,
    triggerUpdateAllSettingsOwners,
    updateUserSettings,
} from "@/Api/ApiCalls";
import { queryKeys } from "@/Api/query";
import type {
    SettingsMissingOwnerSchema,
    SettingsOwnerSchema,
    UserSettingsSchema,
} from "@/Api/schema";
import {
    BaseOwnerSettingsSection,
    UnregisteredModal,
    BaseUserSettingsCard,
} from "@/Components/Base/BaseSettings";

export const SettingsPage: React.FC = () => {
    const { t } = useTranslation();
    const queryClient = useQueryClient();

    // Cooldown & Feedback States
    const [globalCooldown, setGlobalCooldown] = useState(0);
    const [updatingOwnerId, setUpdatingOwnerId] = useState<number | null>(null);
    const [unregisteredOwner, setUnregisteredOwner] = useState<SettingsOwnerSchema | null>(null);
    const [ownerCooldowns, setOwnerCooldowns] = useState<Record<number, number>>({});
    const [feedbackMsg, setFeedbackMsg] = useState<{
        variant: "success" | "danger";
        text: string;
    } | null>(null);

    useEffect(() => {
        if (globalCooldown <= 0) return;
        const timer = setInterval(() => {
            setGlobalCooldown((prev) => (prev > 0 ? prev - 1 : 0));
        }, 1000);
        return () => clearInterval(timer);
    }, [globalCooldown]);

    useEffect(() => {
        const activeCooldowns = Object.values(ownerCooldowns).some((v) => v > 0);
        if (!activeCooldowns) return;
        const timer = setInterval(() => {
            setOwnerCooldowns((prev) => {
                const next: Record<number, number> = {};
                for (const [key, val] of Object.entries(prev)) {
                    if (val > 1) next[Number(key)] = val - 1;
                }
                return next;
            });
        }, 1000);
        return () => clearInterval(timer);
    }, [ownerCooldowns]);

    const { data, isLoading, isError } = useQuery({
        queryKey: queryKeys.UserSettings,
        queryFn: loadUserSettings,
    });

    const {
        data: ownersData,
        isLoading: isLoadingOwners,
        isError: isErrorOwners,
    } = useQuery({
        queryKey: queryKeys.SettingsOwners,
        queryFn: loadSettingsOwners,
        refetchInterval: 30000,
        refetchIntervalInBackground: false,
    });

    const {
        data: unregisteredData,
        isLoading: isLoadingUnregistered,
        isError: isErrorUnregistered,
    } = useQuery({
        queryKey: queryKeys.SettingsUnregistered(
            unregisteredOwner?.owner_type ?? "",
            unregisteredOwner?.id ?? 0,
        ),
        queryFn: () => loadSettingsUnregistered(unregisteredOwner!.owner_type, unregisteredOwner!.id),
        enabled: !!unregisteredOwner,
    });

    const effectiveGlobalCooldown = Math.max(
        globalCooldown,
        ownersData?.cooldown_seconds ?? 0,
    );

    const invalidateQueries = () => {
        queryClient.invalidateQueries({ queryKey: queryKeys.SettingsOwners });
        queryClient.invalidateQueries({ queryKey: queryKeys.Overview });
        queryClient.invalidateQueries({ queryKey: queryKeys.Menu });
    };

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

    const updateAllMutation = useMutation({
        mutationFn: triggerUpdateAllSettingsOwners,
        onSuccess: (res) => {
            setFeedbackMsg({
                variant: "success",
                text: res.message || t("Update task queued for all owners."),
            });
            setGlobalCooldown(300);
            invalidateQueries();
            setTimeout(() => setFeedbackMsg(null), 5000);
        },
        onError: (err: unknown) => {
            setFeedbackMsg({
                variant: "danger",
                text: err instanceof Error ? err.message : t("Failed to queue update all task."),
            });
            setTimeout(() => setFeedbackMsg(null), 5000);
        },
    });

    const updateSingleMutation = useMutation({
        mutationFn: (owner: SettingsOwnerSchema) =>
            triggerSettingsOwnerUpdate(owner.owner_type, owner.id),
        onSuccess: (res, owner) => {
            setFeedbackMsg({
                variant: "success",
                text: res.message || t("Owner update initiated successfully."),
            });
            setOwnerCooldowns((prev) => ({ ...prev, [owner.id]: 60 }));
            invalidateQueries();
            setTimeout(() => setFeedbackMsg(null), 5000);
        },
        onError: (err: unknown) => {
            setFeedbackMsg({
                variant: "danger",
                text: err instanceof Error ? err.message : t("Failed to trigger owner update."),
            });
            setTimeout(() => setFeedbackMsg(null), 5000);
        },
        onSettled: () => {
            setUpdatingOwnerId(null);
        },
    });

    const deleteMutation = useMutation({
        mutationFn: (owner: SettingsOwnerSchema) =>
            deleteSettingsOwner(owner.owner_type, owner.id),
        onSuccess: (res) => {
            setFeedbackMsg({
                variant: "success",
                text: res.message || t("Owner removed successfully."),
            });
            invalidateQueries();
            setTimeout(() => setFeedbackMsg(null), 5000);
        },
        onError: (err: unknown) => {
            setFeedbackMsg({
                variant: "danger",
                text: err instanceof Error ? err.message : t("Failed to delete owner."),
            });
            setTimeout(() => setFeedbackMsg(null), 5000);
        },
    });

    const handleTriggerSingleUpdate = (ownerId: number) => {
        const owner = ownersData?.registered.find((o) => o.id === ownerId);
        if (!owner) return;
        setUpdatingOwnerId(ownerId);
        updateSingleMutation.mutate(owner);
    };

    const handleDeleteOwner = async (owner: SettingsOwnerSchema) => {
        await deleteMutation.mutateAsync(owner);
    };

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
        <Card className={`${styles["page"]} border-0`}>
            <Card.Body className="bg-dark-body">
                {/* Page Header */}
                <Card.Header className={styles["header"] + " bg-dark"}>
                    <Settings2 size={24} aria-hidden="true" color="royalblue" />
                    <div>
                        <h1 className={styles["title"]}>{t("Settings")}</h1>
                        <p className={styles["description"]}>
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
                    globalCooldown={effectiveGlobalCooldown}
                    isUpdatingAll={updateAllMutation.isPending}
                    onUpdateAll={() => updateAllMutation.mutate()}
                    feedbackMessage={feedbackMsg}
                    onDismissFeedback={() => setFeedbackMsg(null)}
                    onTriggerSingleUpdate={handleTriggerSingleUpdate}
                    updatingOwnerId={updatingOwnerId}
                    ownerCooldowns={ownerCooldowns}
                    onDeleteOwner={handleDeleteOwner}
                    isDeleting={deleteMutation.isPending}
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
