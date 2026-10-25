// React
import type React from "react";

// Third Party
import { Building2, Shield, User } from "lucide-react";

// Styles
// AA Ledger
import styles from "@/Components/Base/OwnerPortrait/OwnerPortrait.module.css";

export interface OwnerPortraitProps {
  /** Image URL. Without it the owner type icon is shown instead. */
  src?: string | null;
  alt?: string;
  /** Owner type, selects the fallback icon. */
  type?: string;
  /** `sm` = 32 px, `lg` = 48 px. */
  size?: "sm" | "lg";
  /** `circle` (default) or `rounded` (square with rounded corners). */
  shape?: "circle" | "rounded";
  /** Adds a border around the portrait. */
  bordered?: boolean;
  className?: string;
}

const ICONS = {
  corporation: Building2,
  alliance: Shield,
} as const;

/**
 * Portrait of a character, corporation or alliance.
 * Shows the image, or the matching type icon when no image URL is available.
 */
export const OwnerPortrait: React.FC<OwnerPortraitProps> = ({
  src,
  alt = "",
  type = "character",
  size = "lg",
  shape = "circle",
  bordered = false,
  className = "",
}) => {
  const classes = [
    styles[size],
    shape === "circle" ? "rounded-circle" : "rounded",
    bordered ? "border border-2 border-secondary" : "",
    "flex-shrink-0",
    className,
  ]
    .filter(Boolean)
    .join(" ");

  if (src) {
    return <img src={src} alt={alt} className={`${classes} object-fit-cover`} loading="lazy" />;
  }

  const Icon = ICONS[type as keyof typeof ICONS] ?? User;
  return (
    <div
      className={`${classes} bg-secondary text-light d-flex align-items-center justify-content-center`}
      role="img"
      aria-label={alt || undefined}
      aria-hidden={alt ? undefined : true}
    >
      <Icon size={size === "lg" ? 24 : 16} />
    </div>
  );
};

export default OwnerPortrait;
