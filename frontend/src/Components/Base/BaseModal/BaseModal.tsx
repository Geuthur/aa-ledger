// React
import { useState } from "react";
import type { ReactNode } from "react";

// Third Party
import { Alert, Button, Modal } from "react-bootstrap";
import { useTranslation } from "react-i18next";

import { MODAL_DEFAULTS } from "@/Components/Base/BaseModal/BaseModalProps";
import type {
  BaseModalProps,
  BaseModalSharedProps,
  ConfirmModalProps,
  DefaultModalProps,
  ModalFormData,
} from "@/Components/Base/BaseModal/BaseModalProps";

interface ModalShellProps extends BaseModalSharedProps {
  show: boolean;
  onHide: () => void;
  onEnter?: () => void;
  title: ReactNode;
  footer: ReactNode | null;
  children?: ReactNode;
}

/** Gemeinsamer Rahmen (Header / Body / Footer) für alle Varianten. */
function ModalShell({
  show,
  onHide,
  onEnter,
  onShow,
  onExited,
  title,
  footer,
  children,
  size = MODAL_DEFAULTS.size,
  centered = MODAL_DEFAULTS.centered,
  scrollable = MODAL_DEFAULTS.scrollable,
  backdrop = MODAL_DEFAULTS.backdrop,
  restoreFocus = MODAL_DEFAULTS.restoreFocus,
  closeButton = MODAL_DEFAULTS.closeButton,
  className,
  bodyClassName,
  titleClassName,
}: ModalShellProps) {
  // Behalte Inhalte während der Schließen-Animation bei, damit das Modal nicht leer aufblitzt
  const [cachedContent, setCachedContent] = useState<{
    title: ReactNode;
    children: ReactNode;
    footer: ReactNode | null;
  }>({
    title,
    children,
    footer,
  });

  if (show) {
    if (
      (title !== undefined && title !== null && title !== cachedContent.title) ||
      (children !== undefined && children !== null && children !== false && children !== cachedContent.children) ||
      (footer !== undefined && footer !== cachedContent.footer)
    ) {
      setCachedContent({
        title: title ?? cachedContent.title,
        children: children ?? cachedContent.children,
        footer: footer !== undefined ? footer : cachedContent.footer,
      });
    }
  }

  const displayedTitle = show ? title : (cachedContent.title ?? title);
  const displayedChildren = show ? children : (cachedContent.children ?? children);
  const displayedFooter = show ? footer : (cachedContent.footer ?? footer);

  return (
    <Modal
      show={show}
      size={size}
      onHide={onHide}
      onEnter={onEnter}
      onShow={onShow}
      onExited={onExited}
      centered={centered}
      scrollable={scrollable}
      backdrop={backdrop}
      restoreFocus={restoreFocus}
      dialogClassName={className}
    >
      <Modal.Header closeButton={closeButton}>
        <Modal.Title className={titleClassName}>{displayedTitle}</Modal.Title>
      </Modal.Header>
      <Modal.Body className={bodyClassName}>{displayedChildren}</Modal.Body>
      {displayedFooter !== null && <Modal.Footer>{displayedFooter}</Modal.Footer>}
    </Modal>
  );
}

/** Normales Modal: zeigt nur die übergebenen Children an. */
function DefaultModal({
  show,
  onHide,
  title,
  children,
  footer,
  hideFooter = false,
  closeText,
  closeVariant = MODAL_DEFAULTS.closeVariant,
  ...shared
}: DefaultModalProps) {
  const { t } = useTranslation();

  const defaultFooter = (
    <Button variant={closeVariant} onClick={onHide}>
      {closeText ?? t("Close")}
    </Button>
  );

  return (
    <ModalShell
      {...shared}
      show={show}
      onHide={onHide}
      title={title}
      footer={hideFooter ? null : (footer ?? defaultFooter)}
    >
      {children}
    </ModalShell>
  );
}

/** Bestätigungs-Modal: verarbeitet Daten über `onApprove` (optional mit Formular). */
function ConfirmModal({
  data: ModalData,
  showModal,
  setShowModal,
  onApprove,
  isPending = false,
  validate,
  initialFormData,
  title,
  confirmText,
  confirmVariant,
  closeText,
  closeVariant = MODAL_DEFAULTS.closeVariant,
  children,
  onEnter,
  onExited,
  ...shared
}: ConfirmModalProps) {
  const { t } = useTranslation();
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [formData, setFormData] = useState<ModalFormData>(initialFormData ?? {});
  const [validated, setValidated] = useState(false);

  // Behalte ModalData während der Exit-Animation bei
  const [cachedData, setCachedData] = useState(ModalData);
  if (showModal && ModalData && ModalData !== cachedData) {
    setCachedData(ModalData);
  }
  const effectiveData = showModal ? ModalData : (ModalData ?? cachedData);

  const resetState = () => {
    setErrorMessage(null);
    setFormData(initialFormData ?? {});
    setValidated(false);
  };

  const handleClose = () => {
    // Nicht sofort resetten, damit Formular/Fehler während der Animation sichtbar bleiben
    setShowModal(false);
  };

  const handleEnter = () => {
    resetState();
    onEnter?.();
  };

  const handleExited = () => {
    resetState();
    onExited?.();
  };

  const handleApprove = async () => {
    if (validate && !validate(formData)) {
      setValidated(true);
      return;
    }
    try {
      await onApprove({ url: effectiveData.url, formData });
      // Erfolgreich: Modal schließen, Reset erfolgt in onExited
      setShowModal(false);
    } catch (error: unknown) {
      setErrorMessage(error instanceof Error ? error.message : 'An unexpected error occurred.');
    }
  };

  const renderedChildren =
    typeof children === 'function'
      ? children({ formData, onChange: setFormData })
      : children;

  const footer = (
    <>
      <Button
        variant={confirmVariant ?? effectiveData.color ?? MODAL_DEFAULTS.confirmVariant}
        disabled={isPending}
        onClick={handleApprove}
      >
        {isPending ? t("Loading...") : confirmText || effectiveData.buttonText || t("Confirm")}
      </Button>
      <Button variant={closeVariant} onClick={handleClose}>
        {closeText ?? t("Close")}
      </Button>
    </>
  );

  return (
    <ModalShell
      {...shared}
      show={showModal}
      onHide={handleClose}
      onEnter={handleEnter}
      onExited={handleExited}
      title={title ?? effectiveData.title}
      footer={footer}
    >
      {errorMessage && (
        <Alert variant="danger" onClose={() => setErrorMessage(null)} dismissible>
          {errorMessage}
        </Alert>
      )}
      <div className={validated ? 'was-validated' : ''}>
        {renderedChildren}
      </div>
    </ModalShell>
  );
}

/**
 * BaseModal mit zwei Varianten:
 * - `variant="default"` (Standard): normales Modal, Body = `children`, Footer = Schließen-Button.
 * - `variant="confirm"`: Bestätigungs-Modal mit `onApprove`, optional Formular via Render-Children.
 *
 * Alle Darstellungs-Werte (size, centered, backdrop, ...) sind optional und
 * fallen auf `MODAL_DEFAULTS` zurück.
 */
function BaseModal(props: BaseModalProps) {
  if (props.variant === "confirm" || "showModal" in props || "data" in props) {
    return <ConfirmModal {...(props as ConfirmModalProps)} />;
  }
  return <DefaultModal {...(props as DefaultModalProps)} />;
}

export default BaseModal;
