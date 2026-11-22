// React
import { useState } from "react";

// Third Party
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { queryKeys, useCooldown, useFeedback, useOwnerCooldowns } from "aa-geuthur-react";
import { useTranslation } from "react-i18next";

// AA Ledger
import { overviewQueryKeys } from "@/Api/calls/overview";
import {
  deleteSettingsOwner,
  loadSettingsOwners,
  settingsQueryKeys,
  triggerSettingsOwnerUpdate,
  triggerUpdateAllSettingsOwners,
} from "@/Api/calls/settings";
import type { SettingsOwnerSchema } from "@/Api/schema";

/** Loads the registered and missing owners, refreshed every 30 seconds. */
export function useSettingsOwners() {
  return useQuery({
    queryKey: settingsQueryKeys.owners,
    queryFn: loadSettingsOwners,
    refetchInterval: 30000,
    refetchIntervalInBackground: false,
  });
}

/**
 * Update-all, single update and delete for the owners on the settings page,
 * including feedback messages and cooldowns.
 * @param owners The registered owners (used to find an owner by id)
 * @param serverCooldown Remaining cooldown reported by the server in seconds
 */
export function useSettingsOwnerActions(
  owners: SettingsOwnerSchema[] = [],
  serverCooldown = 0,
) {
  const { t } = useTranslation();
  const queryClient = useQueryClient();
  const { seconds: globalCooldown, start: startGlobalCooldown } = useCooldown();
  const { cooldowns: ownerCooldowns, start: startOwnerCooldown } = useOwnerCooldowns();
  const { feedback, showFeedback, clearFeedback } = useFeedback();
  const [updatingOwnerId, setUpdatingOwnerId] = useState<number | null>(null);

  const invalidateQueries = () => {
    queryClient.invalidateQueries({ queryKey: settingsQueryKeys.owners });
    queryClient.invalidateQueries({ queryKey: overviewQueryKeys.overview });
    queryClient.invalidateQueries({ queryKey: queryKeys.Menu });
  };

  const updateAllMutation = useMutation({
    mutationFn: triggerUpdateAllSettingsOwners,
    onSuccess: (res) => {
      showFeedback("success", res.message || t("Update task queued for all owners."));
      startGlobalCooldown(300);
      invalidateQueries();
    },
    onError: (err: unknown) => {
      showFeedback(
        "danger",
        err instanceof Error ? err.message : t("Failed to queue update all task."),
      );
    },
  });

  const updateSingleMutation = useMutation({
    mutationFn: (owner: SettingsOwnerSchema) =>
      triggerSettingsOwnerUpdate(owner.owner_type, owner.id),
    onSuccess: (res, owner) => {
      showFeedback("success", res.message || t("Owner update initiated successfully."));
      startOwnerCooldown(owner.id, 60);
      invalidateQueries();
    },
    onError: (err: unknown) => {
      showFeedback(
        "danger",
        err instanceof Error ? err.message : t("Failed to trigger owner update."),
      );
    },
    onSettled: () => {
      setUpdatingOwnerId(null);
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (owner: SettingsOwnerSchema) =>
      deleteSettingsOwner(owner.owner_type, owner.id),
    onSuccess: (res) => {
      showFeedback("success", res.message || t("Owner removed successfully."));
      invalidateQueries();
    },
    onError: (err: unknown) => {
      showFeedback("danger", err instanceof Error ? err.message : t("Failed to delete owner."));
    },
  });

  const updateOwner = (ownerId: number) => {
    const owner = owners.find((o) => o.id === ownerId);
    if (!owner) return;
    setUpdatingOwnerId(ownerId);
    updateSingleMutation.mutate(owner);
  };

  return {
    feedback,
    clearFeedback,
    globalCooldown: Math.max(globalCooldown, serverCooldown),
    ownerCooldowns,
    updatingOwnerId,
    updateAll: () => updateAllMutation.mutate(),
    isUpdatingAll: updateAllMutation.isPending,
    updateOwner,
    deleteOwner: (owner: SettingsOwnerSchema) => deleteMutation.mutateAsync(owner),
    isDeleting: deleteMutation.isPending,
  };
}
