// Third Party
import { describe, expect, it } from 'vitest';

// AA Example
import {
    characterImageUrl,
    formatEveTime,
    formatNumber,
    formatRelativeTime,
    getSecColor,
    shipImageUrl,
} from '@/Utils/eveOnline';

describe('eveOnline utils', () => {
    describe('shipImageUrl', () => {
        it('should return correct ship image url with default size', () => {
            // Test Data
            const typeId = 587;

            // Test Action
            const url = shipImageUrl(typeId);

            // Expected Result
            expect(url).toBe('https://images.evetech.net/types/587/render?size=512');
        });

        it('should return correct ship image url with custom size', () => {
            // Test Data
            const typeId = 587;
            const size = 128;

            // Test Action
            const url = shipImageUrl(typeId, size);

            // Expected Result
            expect(url).toBe('https://images.evetech.net/types/587/render?size=128');
        });
    });

    describe('characterImageUrl', () => {
        it('should return correct portrait url with default size', () => {
            // Test Data
            const characterId = 98000001;

            // Test Action
            const url = characterImageUrl(characterId);

            // Expected Result
            expect(url).toBe('https://images.evetech.net/characters/98000001/portrait?size=512');
        });

        it('should return correct portrait url with custom size', () => {
            // Test Data
            const characterId = 98000001;
            const size = 256;

            // Test Action
            const url = characterImageUrl(characterId, size);

            // Expected Result
            expect(url).toBe('https://images.evetech.net/characters/98000001/portrait?size=256');
        });
    });

    describe('getSecColor', () => {
        it('should return hisec badge for highsec (>= 0.5)', () => {
            // Test Data
            const sec = 0.9;

            // Test Action
            const classes = getSecColor(sec);

            // Expected Result
            expect(classes).toBe('aa-badge-hisec');
        });

        it('should return lowsec badge for lowsec (> 0.0 and < 0.5)', () => {
            // Test Data
            const sec = 0.4;

            // Test Action
            const classes = getSecColor(sec);

            // Expected Result
            expect(classes).toBe('aa-badge-lowsec');
        });

        it('should return nullsec badge for nullsec/wormholes (<= 0.0)', () => {
            // Test Data
            const sec = -0.2;

            // Test Action
            const classes = getSecColor(sec);

            // Expected Result
            expect(classes).toBe('aa-badge-nullsec');
        });
    });

    describe('formatEveTime', () => {
        it('should format a given Date into EVE time string HH:MM:SS EVE in UTC', () => {
            // Test Data
            const testDate = new Date(Date.UTC(2026, 8, 29, 14, 5, 9));

            // Test Action
            const formatted = formatEveTime(testDate);

            // Expected Result
            expect(formatted).toBe('14:05:09 EVE');
        });
    });

    describe('formatNumber', () => {
        it('should format billions with B suffix', () => {
            // Test Data
            const value = 2_500_000_000;

            // Test Action
            const formatted = formatNumber(value, 'ISK');

            // Expected Result
            expect(formatted).toBe('2.50B ISK');
        });

        it('should format millions with M suffix', () => {
            // Test Data
            const value = 12_400_000;

            // Test Action
            const formatted = formatNumber(value, 'ISK');

            // Expected Result
            expect(formatted).toBe('12.4M ISK');
        });

        it('should format thousands with K suffix', () => {
            // Test Data
            const value = 5_200;

            // Test Action
            const formatted = formatNumber(value, 'ISK');

            // Expected Result
            expect(formatted).toBe('5.2K ISK');
        });

        it('should format small numbers using standard number format', () => {
            // Test Data
            const value = 42;

            // Test Action
            const formatted = formatNumber(value, 'ISK', 'en-US');

            // Expected Result
            expect(formatted).toBe('42 ISK');
        });

        it('should format without unit when unit is empty string', () => {
            // Test Data
            const value = 1_500_000;

            // Test Action
            const formatted = formatNumber(value, '');

            // Expected Result
            expect(formatted).toBe('1.5M');
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
});
