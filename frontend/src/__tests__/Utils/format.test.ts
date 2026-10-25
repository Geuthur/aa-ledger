// Third Party
import { describe, expect, it } from 'vitest';

// AA Example
import {
    formatCompactNumber,
    formatDate,
    formatEta,
    formatIsk,
    formatNumber,
    formatRelativeTime,
} from '@/Utils/format';

describe('format utils', () => {
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
        it('should return N/A for null, undefined or invalid date', () => {
            // Test Data & Test Action & Expected Result
            expect(formatRelativeTime(null)).toBe('N/A');
            expect(formatRelativeTime(undefined)).toBe('N/A');
            expect(formatRelativeTime('invalid-date')).toBe('N/A');
        });

        it('should format past date into relative time string', () => {
            // Test Data
            const pastDate = new Date(Date.now() - 3600 * 1000);

            // Test Action
            const formatted = formatRelativeTime(pastDate);

            // Expected Result
            expect(formatted).not.toBe('N/A');
            expect(formatted.length).toBeGreaterThan(0);
        });

        it('should format future date into relative time string', () => {
            // Test Data
            const futureDate = new Date(Date.now() + 1800 * 1000);

            // Test Action
            const formatted = formatRelativeTime(futureDate);

            // Expected Result
            expect(formatted).not.toBe('N/A');
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

    describe('formatCompactNumber', () => {
        it('should format billions with B suffix', () => {
            // Test Data
            const value = 2_500_000_000;

            // Test Action
            const formatted = formatCompactNumber(value, 'ISK');

            // Expected Result
            expect(formatted).toBe('2.50B ISK');
        });

        it('should format millions with M suffix', () => {
            // Test Data
            const value = 12_400_000;

            // Test Action
            const formatted = formatCompactNumber(value, 'ISK');

            // Expected Result
            expect(formatted).toBe('12.4M ISK');
        });

        it('should format thousands with K suffix', () => {
            // Test Data
            const value = 5_200;

            // Test Action
            const formatted = formatCompactNumber(value, 'ISK');

            // Expected Result
            expect(formatted).toBe('5.2K ISK');
        });

        it('should format small numbers using standard number format', () => {
            // Test Data
            const value = 42;

            // Test Action
            const formatted = formatCompactNumber(value, 'ISK', 'en-US');

            // Expected Result
            expect(formatted).toBe('42 ISK');
        });

        it('should format without unit when no unit is given', () => {
            // Test Data
            const value = 1_500_000;

            // Test Action
            const formatted = formatCompactNumber(value);

            // Expected Result
            expect(formatted).toBe('1.5M');
        });
    });

    describe('formatIsk', () => {
        it('should round to whole ISK and append the unit', () => {
            // Test Data
            const value = 1234567.89;

            // Test Action
            const formatted = formatIsk(value);

            // Expected Result
            expect(formatted).toBe('1,234,568 ISK');
        });
    });
});
