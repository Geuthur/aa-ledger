// React
import { useState } from "react";

// Third Party
import { Alert, Button, Modal } from "react-bootstrap";
import { useTranslation } from "react-i18next";

import { ModalSize } from "@/Components/Modals/BaseModal/BaseModalProps";
import type { ModalData } from "@/Components/Modals/BaseModal/BaseModalProps";

type FormData = Record<string, string | boolean>;

function BaseModal({
  data: ModalData,
  showModal,
  onApprove,
  setShowModal,
  isPending = false, // <-- NEU: Ladezustand von der Mutation
  validate,
  initialFormData,
  size,
  children,
}: {
  data: ModalData;
  showModal: boolean;
  onApprove: (data: { url: string; formData?: FormData }) => Promise<unknown>;
  setShowModal: (show: boolean) => void;
  isPending?: boolean;
  validate?: (formData: FormData) => boolean;
  initialFormData?: FormData;
  size?: ModalSize;
  children?: React.ReactNode | ((props: { formData: FormData; onChange: (data: FormData) => void }) => React.ReactNode);
}) {
  const { t } = useTranslation();
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [formData, setFormData] = useState<FormData>(initialFormData ?? {});
  const [validated, setValidated] = useState(false);
  const handleClose = () => {
    setErrorMessage(null);
    setFormData(initialFormData ?? {});
    setValidated(false);
    setShowModal(false);
  };
  const handleEnter = () => {
    setErrorMessage(null);
    setFormData(initialFormData ?? {});
    setValidated(false);
  };
  const handleApprove = async () => {
    if (validate && !validate(formData)) {
      setValidated(true);
      return;
    }
    try {
      await onApprove({ url: ModalData.url, formData });
      // Erfolgreich:
      setErrorMessage(null);
      setFormData(initialFormData ?? {});
      setValidated(false);
      setShowModal(false);
    } catch (error: unknown) {
      setErrorMessage(error instanceof Error ? error.message : 'An unexpected error occurred.');
    }
  };

  const renderedChildren =
    typeof children === 'function'
      ? children({ formData, onChange: setFormData })
      : children;

  return (
    <Modal
      show={showModal}
      size={size ?? ModalSize.large}
      onHide={handleClose}
      onEnter={handleEnter}
      centered={true}
      restoreFocus={false} // Prevent the modal from stealing focus when it is closed
    >
      <Modal.Header closeButton>
        <Modal.Title>{ModalData.title}</Modal.Title>
      </Modal.Header>
      <Modal.Body>
        {errorMessage && (
          <Alert variant="danger" onClose={() => setErrorMessage(null)} dismissible>
            {errorMessage}
          </Alert>
        )}
        <div className={validated ? 'was-validated' : ''}>
          {renderedChildren}
        </div>
      </Modal.Body>
      <Modal.Footer>
        <Button variant={ModalData.color ?? "success"} disabled={isPending} onClick={handleApprove}>
          {isPending ? t("Loading...") : ModalData.buttonText || t("Confirm")}
        </Button>
        <Button onClick={handleClose}>
          {t("Close")}
        </Button>
      </Modal.Footer>
    </Modal>
  );
}

export default BaseModal;
