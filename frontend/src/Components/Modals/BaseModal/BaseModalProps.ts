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
