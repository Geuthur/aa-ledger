// React
import React from "react";

// Third Party
import { Badge } from "react-bootstrap";
import { useTranslation } from "react-i18next";

// AA Ledger
import BaseModal, { ModalSize } from "@/Components/Base/BaseModal";

/** Props of the modal that shows the full error message of an owner. */
export interface AdministrationErrorModalProps {
  show: boolean;
  onHide: () => void;
  ownerName: string;
  status: string;
  /** Full error message. When empty, a default text is shown for `token_error`. */
  errorMessage?: string | null;
  /** Bootstrap variant of the status badge. */
  statusVariant?: string;
}

/**
 * Shows the owner name, the status and the complete error message of an owner.
 * Opened by clicking the status badge in `AdministrationOwnersTable`.
 */
export const AdministrationErrorModal: React.FC<AdministrationErrorModalProps> = ({
  show,
  onHide,
  ownerName,
  status,
  errorMessage,
  statusVariant = "danger",
}) => {
  const { t } = useTranslation();

  const message =
    errorMessage ||
    (status === "token_error"
      ? t("The ESI token is invalid or expired. Re-add the character or corporation.")
      : t("No error message available."));

  return (
    <BaseModal
      show={show}
      onHide={onHide}
      size={ModalSize.large}
      title={t("Error details of {{name}}", { name: ownerName })}
    >
      <div className="d-flex align-items-center gap-2 mb-3">
        <span className="fw-semibold">{ownerName}</span>
        <Badge bg={statusVariant} data-testid="error-modal-status">
          {status}
        </Badge>
      </div>
      <pre className="text-break text-wrap mb-0" data-testid="error-modal-message">
        {message}
      </pre>
    </BaseModal>
  );
};

export default AdministrationErrorModal;
