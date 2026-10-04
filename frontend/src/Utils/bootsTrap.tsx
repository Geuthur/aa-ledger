// Third Party
import OverlayTrigger from "react-bootstrap/OverlayTrigger";
import Tooltip from "react-bootstrap/Tooltip";

// Styles
import styles from '@/Utils/bootsTrap.module.css';

/**
 * Tooltip notification component
 * @param toastNotice The message to display inside the tooltip
 * @returns A React element representing the tooltip container
 */
export function toolTipContainer(message: string): React.ReactElement {
    return (
        <div className={styles.tooltip}>
            <span>{message}</span>
        </div>
    );
}

/**
 * Helper function for rendering tooltips
 * @param message The message to display inside the tooltip
 * @param children The React element that triggers the tooltip
 */
export function renderTooltip(
    message: string,
    children: React.ComponentProps<typeof OverlayTrigger>["children"],
) {
    return (
        <OverlayTrigger
            placement="auto"
            trigger={["hover", "focus"]}
            overlay={
                <Tooltip id="vowra" className={styles["tooltip-z-index"]}>
                    {message}
                </Tooltip>
            }
        >
            {children}
        </OverlayTrigger>
    );
}
