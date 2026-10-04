// React
import React from 'react';

// Third Party
import { useTranslation } from 'react-i18next';

// Voices of War
import { formatLastFetch, useLivePing } from '@/Components/Badges/liveStatusHelper';
import { renderTooltip } from '@/Utils';

export interface LiveStatusProps {
    /** Whether a query or operation encountered an error */
    isError?: boolean;
    /** Optional error object or message for detailed display */
    error?: unknown;
    /** Whether a query or operation is currently loading */
    isLoading?: boolean;
    /** Whether a query is actively fetching (including background refetches) */
    isFetching?: boolean;
    /** Timestamp in ms of the last successful data update */
    dataUpdatedAt?: number;
    /** Whether to display the formatted last fetch timestamp alongside the dot */
    showTimestamp?: boolean;
    /** Optional prefix before the timestamp (default: '↻') */
    timestampPrefix?: string;
    /** Duration in ms for the ping animation on fresh fetch (default: 2000) */
    pingDuration?: number;
    /** Wrapper container className */
    className?: string;
    /** Custom dot className */
    dotClassName?: string;
    /** Custom timestamp text className */
    textClassName?: string;
    /** Optional children rendered beside the dot */
    children?: React.ReactNode;
}

/**
 * Reusable Live Status Indicator component:
 * - Red dot when an error occurred (isError)
 * - Orange pulsing dot while loading or fetching (isLoading / isFetching)
 * - Green dot when idle/ready with temporary ping pulse animation upon new data
 * - Optional timestamp display ("↻ 19:10:24 EVE", "Lädt…", or "Fehler")
 */
export function LiveStatusIndicator({
    isError = false,
    error,
    isLoading = false,
    isFetching = false,
    dataUpdatedAt,
    showTimestamp = false,
    timestampPrefix = '↻',
    pingDuration = 2000,
    className = 'aa-status-indicator',
    dotClassName = '',
    textClassName = 'aa-status-text',
    children,
}: LiveStatusProps) {
    const { t } = useTranslation();
    const isBusy = isLoading || isFetching;
    const pinging = useLivePing(dataUpdatedAt, isBusy || isError, pingDuration);

    const errorMessage = error instanceof Error
        ? error.message
        : typeof error === 'string'
            ? error
            : t('Fehler beim Laden');

    const tooltipText = isError
        ? errorMessage
        : isBusy
            ? t('Lädt…')
            : dataUpdatedAt
                ? `${t('Last Fetch')}: ${formatLastFetch(dataUpdatedAt)}`
                : t('Kein Fetch');

    return (
        <>
            {renderTooltip(
                tooltipText,
                <span className={className}>
                    {/* Status Dot */}
                    <span className={`aa-status-dot ${dotClassName}`}>
                        {isError ? (
                            <span className="aa-status-dot-fill aa-status-dot-error" />
                        ) : isBusy ? (
                            <span className="aa-status-dot-fill aa-status-dot-busy" />
                        ) : (
                            <>
                                {pinging && (
                                    <span className="aa-status-ping" />
                                )}
                                <span className="aa-status-dot-fill aa-status-dot-ready" />
                            </>
                        )}
                    </span>

                    {/* Optional Children */}
                    {children}

                    {/* Optional Timestamp */}
                    {showTimestamp && (
                        <span className={isError ? 'aa-status-text aa-status-text-error' : textClassName}>
                            {isError
                                ? t('Fehler')
                                : isBusy
                                    ? t('Lädt…')
                                    : dataUpdatedAt
                                        ? `${timestampPrefix} ${formatLastFetch(dataUpdatedAt)}`
                                        : t('Kein Fetch')}
                        </span>
                    )}
                </span>
            )}
        </>
    );
}
