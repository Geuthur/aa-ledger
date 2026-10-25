// React
import { useState } from "react";

// Third Party
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

// AA Ledger
import {
  deleteAdministrationOwner,
  loadAdministrationOwners,
  loadUserData,
  queueUpdate,
  triggerAdministrationOwnerUpdate,
} from "@/Api/ApiCalls";
import { queryKeys } from "@/Api/query";

export interface TaskFeedback {
  variant: "success" | "danger";
  message: string;
}

/** Loads all owners of the Administration. */
export function useAdministrationOwners() {
  return useQuery({
    queryKey: queryKeys.AdministrationOwners,
    queryFn: loadAdministrationOwners,
  });
}

/** Tells whether the current user is a superuser (global update tasks, force refresh). */
export function useIsSuperuser() {
  const { data } = useQuery({
    queryKey: queryKeys.User,
    queryFn: loadUserData,
  });
  return data?.user.is_superuser ?? false;
}

/**
 * Single owner update, global queue update and delete for the Administration,
 * including the task feedback message.
 * @param onDeleted Called after an owner was deleted successfully
 */
export function useAdministrationActions(onDeleted?: () => void) {
  const queryClient = useQueryClient();
  const [updatingKey, setUpdatingKey] = useState<string | null>(null);
  const [taskFeedback, setTaskFeedback] = useState<TaskFeedback | null>(null);

  const refreshOwners = () =>
    queryClient.invalidateQueries({ queryKey: queryKeys.AdministrationOwners });

  const singleUpdateMutation = useMutation({
    mutationFn: ({
      ownerType,
      ownerId,
      forceRefresh,
    }: {
      ownerType: "character" | "corporation";
      ownerId: number;
      forceRefresh: boolean;
    }) =>
      triggerAdministrationOwnerUpdate(ownerType, ownerId, {
        force_refresh: forceRefresh,
      }),
    onMutate: ({ ownerType, ownerId }) => {
      setUpdatingKey(`${ownerType}-${ownerId}`);
    },
    onSuccess: (data) => {
      setTaskFeedback({ variant: "success", message: data.message });
      refreshOwners();
    },
    onError: (err: Error) => {
      setTaskFeedback({ variant: "danger", message: err.message });
    },
    onSettled: () => {
      setUpdatingKey(null);
    },
  });

  const globalQueueMutation = useMutation({
    mutationFn: ({
      target,
      forceRefresh,
    }: {
      target: "characters" | "corporations";
      forceRefresh: boolean;
    }) =>
      queueUpdate({
        target,
        eve_id: null,
        force_refresh: forceRefresh,
      }),
    onSuccess: (data) => {
      setTaskFeedback({ variant: "success", message: data.message });
      refreshOwners();
    },
    onError: (err: Error) => {
      setTaskFeedback({ variant: "danger", message: err.message });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: ({
      ownerType,
      ownerId,
    }: {
      ownerType: "character" | "corporation";
      ownerId: number;
    }) => deleteAdministrationOwner(ownerType, ownerId),
    onSuccess: (data) => {
      setTaskFeedback({ variant: "success", message: data.message });
      onDeleted?.();
      refreshOwners();
    },
    onError: (err: Error) => {
      setTaskFeedback({ variant: "danger", message: err.message });
    },
  });

  return {
    taskFeedback,
    clearTaskFeedback: () => setTaskFeedback(null),
    updatingKey,
    triggerUpdate: singleUpdateMutation.mutate,
    queueUpdate: globalQueueMutation.mutate,
    isQueuing: globalQueueMutation.isPending,
    deleteOwner: deleteMutation.mutate,
    isDeleting: deleteMutation.isPending,
  };
}
