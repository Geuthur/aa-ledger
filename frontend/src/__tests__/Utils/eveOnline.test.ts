// Third Party
import { describe, expect, it } from 'vitest';

// AA Example
import {
    characterImageUrl,
    formatEveTime,
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
});
