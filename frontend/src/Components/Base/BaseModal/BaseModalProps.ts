// React
import type { ReactNode } from "react";

// Third Party
import type { ModalProps } from "react-bootstrap";

export const ModalSize = {
  small: "sm",
  medium: undefined, // Bootstrap Standardgröße
  large: "lg",
  extraLarge: "xl",
} as const;

export type ModalSize = (typeof ModalSize)[keyof typeof ModalSize];
export type ModalData = {
  title: string;
  text: string;
  icon: string;
  modal_id: string;
  url: string;
  color?: string | null;
  buttonText?: string | null;
};

export type ModalFormData = Record<string, string | boolean>;

/**
 * Optionale Werte, die beide Varianten teilen.
 * Alles, was nicht gesetzt wird, fällt auf `MODAL_DEFAULTS` zurück.
 */
export interface BaseModalSharedProps {
  /** Modal-Größe (Standard: `ModalSize.large`) */
  size?: ModalSize;
  /** Vertikal zentriert (Standard: `true`) */
  centered?: boolean;
  /** Body scrollbar statt ganzes Modal (Standard: `false`) */
  scrollable?: boolean;
  /** Backdrop-Verhalten, z.B. `"static"` (Standard: `true`) */
  backdrop?: ModalProps["backdrop"];
  /** Fokus beim Schließen zurückgeben (Standard: `false`) */
  restoreFocus?: boolean;
  /** "X" im Header anzeigen (Standard: `true`) */
  closeButton?: boolean;
  /** Text des Schließen-Buttons (Standard: `t("Close")`) */
  closeText?: string;
  /** Bootstrap-Variante des Schließen-Buttons (Standard: `"primary"`) */
  closeVariant?: string;
  /** Zusätzliche Klasse für das Modal-Dialog-Element */
  className?: string;
  /** Zusätzliche Klasse für den Modal-Body */
  bodyClassName?: string;
  /** Zusätzliche Klasse für den Modal-Titel (z.B. Icon + Text) */
  titleClassName?: string;
  /** Wird aufgerufen, sobald das Modal angezeigt wird */
  onShow?: () => void;
  /** Wird aufgerufen, kurz bevor das Modal eingeblendet wird */
  onEnter?: () => void;
  /** Wird aufgerufen, nachdem das Modal komplett ausgeblendet wurde */
  onExited?: () => void;
}

/** Normales Modal: Titel + beliebige React-Children + Schließen-Button. */
export interface DefaultModalProps extends BaseModalSharedProps {
  variant?: "default";
  show: boolean;
  onHide: () => void;
  title: ReactNode;
  children?: ReactNode;
  /** Ersetzt den Standard-Footer (Schließen-Button) */
  footer?: ReactNode;
  /** Footer komplett ausblenden */
  hideFooter?: boolean;
}

export type ConfirmModalChildren =
  | ReactNode
  | ((props: { formData: ModalFormData; onChange: (data: ModalFormData) => void }) => ReactNode);

/** Bestätigungs-Modal: verarbeitet Daten (optional Formular) über `onApprove`. */
export interface ConfirmModalProps extends BaseModalSharedProps {
  variant: "confirm";
  data: ModalData;
  showModal: boolean;
  setShowModal: (show: boolean) => void;
  onApprove: (data: { url: string; formData?: ModalFormData }) => Promise<unknown>;
  isPending?: boolean;
  validate?: (formData: ModalFormData) => boolean;
  initialFormData?: ModalFormData;
  /** Überschreibt `data.title` */
  title?: ReactNode;
  /** Überschreibt `data.buttonText` (Standard: `t("Confirm")`) */
  confirmText?: string;
  /** Überschreibt `data.color` (Standard: `"success"`) */
  confirmVariant?: string;
  children?: ConfirmModalChildren;
}

export type BaseModalProps = DefaultModalProps | ConfirmModalProps;

export const MODAL_DEFAULTS = {
  size: ModalSize.large,
  centered: true,
  scrollable: false,
  backdrop: true,
  restoreFocus: false, // Prevent the modal from stealing focus when it is closed
  closeButton: true,
  closeVariant: "primary",
  confirmVariant: "success",
} as const;
