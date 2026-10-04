// React
import { useCallback } from "react";

// Third Party
import { useQueryState } from "nuqs";

export function useModalQueryState(modalKey = "modal", entityKey = "id") {
  const [activeModal, setActiveModal] = useQueryState(modalKey, {
    clearOnDefault: true,
    defaultValue: "",
  });

  const [activeEntityId, setActiveEntityId] = useQueryState(entityKey, {
    clearOnDefault: true,
    defaultValue: "",
  });

  const openModal = useCallback(
    (modalId: string, entityId?: string) => {
      setActiveModal(modalId);
      if (entityId !== undefined) {
        setActiveEntityId(entityId);
      }
    },
    [setActiveModal, setActiveEntityId],
  );

  const closeModal = useCallback(() => {
    setActiveModal("");
    setActiveEntityId("");
  }, [setActiveModal, setActiveEntityId]);

  return {
    activeModal: activeModal || null,
    activeEntityId: activeEntityId || null,
    openModal,
    closeModal,
    setActiveModal,
  };
}
