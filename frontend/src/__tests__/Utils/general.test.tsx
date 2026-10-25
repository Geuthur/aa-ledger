// Third Party
import { describe, expect, it } from 'vitest';

// AA Example
import { renderHtml } from '@/Utils/general';

describe('general utils', () => {
    describe('renderHtml', () => {
        it('returns a React element with dangerouslySetInnerHTML', () => {
            const element = renderHtml('<strong>Test</strong>');
            expect(element).toBeDefined();
            expect(element.props.dangerouslySetInnerHTML).toEqual({ __html: '<strong>Test</strong>' });
        });
    });
});
