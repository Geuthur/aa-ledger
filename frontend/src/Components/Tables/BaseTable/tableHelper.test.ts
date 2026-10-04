// Third Party
import { describe, expect, it } from 'vitest';

import {
    formatDate,
    formatEta,
    formatNumber,
    formatRelativeTime,
    renderHtml,
} from '@/Components/Tables/BaseTable/tableHelper';

describe('tableHelper functions', () => {
    describe('formatDate', () => {
        it('returns "N/A" for null, undefined or empty string', () => {
            expect(formatDate(null)).toBe('N/A');
            expect(formatDate(undefined)).toBe('N/A');
            expect(formatDate('')).toBe('N/A');
        });

        it('formats a valid date string with default options', () => {
            const dateStr = '2026-09-17T12:00:00Z';
            const formatted = formatDate(dateStr);
            expect(formatted).not.toBe('N/A');
            expect(formatted.length).toBeGreaterThan(0);
        });

        it('formats with custom Intl.DateTimeFormatOptions', () => {
            const dateStr = '2026-09-17T12:00:00Z';
            const formatted = formatDate(dateStr, { year: 'numeric' });
            expect(formatted).toContain('2026');
        });
    });

    describe('formatRelativeTime', () => {
        it('returns "N/A" for falsy or invalid values', () => {
            expect(formatRelativeTime(null)).toBe('N/A');
            expect(formatRelativeTime(undefined)).toBe('N/A');
            expect(formatRelativeTime('invalid-date')).toBe('N/A');
        });

        it('formats a past date relative to now', () => {
            const twoHoursAgo = new Date(Date.now() - 2 * 3600 * 1000);
            const formatted = formatRelativeTime(twoHoursAgo);
            expect(formatted).not.toBe('N/A');
            // e.g. "2 hours ago" or "vor 2 Stunden"
            expect(formatted.length).toBeGreaterThan(0);
        });

        it('formats a future date relative to now', () => {
            const inThirtyMinutes = new Date(Date.now() + 30 * 60 * 1000);
            const formatted = formatRelativeTime(inThirtyMinutes);
            expect(formatted).not.toBe('N/A');
            // e.g. "in 30 minutes" or "in 30 Minuten"
            expect(formatted.length).toBeGreaterThan(0);
        });
    });

    describe('formatEta', () => {
        it('returns "N/A" for missing or invalid dates', () => {
            expect(formatEta(null)).toBe('N/A');
            expect(formatEta('not-a-date')).toBe('N/A');
        });

        it('returns doneLabel when the ETA date is in the past', () => {
            const pastDate = new Date(Date.now() - 10000);
            expect(formatEta(pastDate, 'Done')).toBe('Done');
            expect(formatEta(pastDate, 'Fertig')).toBe('Fertig');
        });

        it('returns relative time when the ETA date is in the future', () => {
            const futureDate = new Date(Date.now() + 60 * 60 * 1000);
            const formatted = formatEta(futureDate, 'Done');
            expect(formatted).not.toBe('Done');
            expect(formatted).not.toBe('N/A');
        });
    });

    describe('formatNumber', () => {
        it('formats a number with default locale', () => {
            expect(formatNumber(1000)).toBe('1,000');
        });

        it('formats a number with specific locale', () => {
            const formattedDe = formatNumber(1000, 'de');
            // In German, 1000 is formatted with a dot or non-breaking space ("1.000")
            expect(formattedDe).toMatch(/1[.\s]000/);
        });

        it('formats with custom options like maximumFractionDigits', () => {
            const formatted = formatNumber(12.3456, 'en', { maximumFractionDigits: 1 });
            expect(formatted).toBe('12.3');
        });
    });

    describe('renderHtml', () => {
        it('returns a React element with dangerouslySetInnerHTML', () => {
            const element = renderHtml('<strong>Test</strong>');
            expect(element).toBeDefined();
            expect(element.props.dangerouslySetInnerHTML).toEqual({ __html: '<strong>Test</strong>' });
        });
    });
});
