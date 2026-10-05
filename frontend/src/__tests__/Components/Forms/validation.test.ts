// Third Party
import { describe, expect, it } from 'vitest';

import {
    hasRequiredFields,
} from '@/Components/Forms/validation';

describe('validation functions', () => {
    describe('hasRequiredFields', () => {
        const validator = hasRequiredFields('foo', 'bar');

        it('returns true when all required fields are present and non-empty', () => {
            expect(validator({ foo: 'val1', bar: 'val2' })).toBe(true);
        });

        it('returns false when a required field is missing', () => {
            expect(validator({ foo: 'val1' })).toBe(false);
        });

        it('returns false when a required field is an empty string or only whitespace', () => {
            expect(validator({ foo: 'val1', bar: '   ' })).toBe(false);
            expect(validator({ foo: '', bar: 'val2' })).toBe(false);
        });

        it('returns false when a required field is not a string', () => {
            expect(validator({ foo: 123, bar: 'val2' } as unknown as Record<string, unknown>)).toBe(false);
        });
    });
});
