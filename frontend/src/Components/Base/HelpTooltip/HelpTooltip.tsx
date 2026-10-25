// React
import type React from "react";

// Third Party
import { CircleHelp } from "lucide-react";

// AA Ledger
import { renderTooltip } from "@/Utils/bootsTrap";

export interface HelpTooltipProps {
  /** Text shown in the tooltip. */
  text: string;
  /** Classes for the icon wrapper, defaults to a muted icon. */
  className?: string;
  /** Icon size in pixels. */
  size?: number;
}

/**
 * Small question mark icon that shows an explanation on hover or focus.
 */
export const HelpTooltip: React.FC<HelpTooltipProps> = ({
  text,
  className = "text-muted",
  size = 14,
}) =>
  renderTooltip(
    text,
    <span className={`d-inline-flex align-items-center cursor-help ${className}`}>
      <CircleHelp size={size} />
    </span>,
  );

export default HelpTooltip;
