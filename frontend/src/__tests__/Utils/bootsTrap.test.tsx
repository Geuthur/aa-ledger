// Third Party
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it } from 'vitest';

// AA Example
import { renderTooltip, toolTipContainer } from '@/Utils/bootsTrap';



describe('bootsTrap utils', () => {
    describe('toolTipContainer', () => {
        it('should render toast notice text correctly', () => {
            // Test Data
            const message = 'Test notification message';

            // Test Action
            render(toolTipContainer(message));

            // Expected Result
            expect(screen.getByText(message)).toBeDefined();
        });
    });

    describe('renderTooltip', () => {
        it('should render trigger child element and display tooltip on hover', async () => {
            // Test Data
            const user = userEvent.setup();
            const message = 'Hover tooltip content';

            // Test Action
            render(
                renderTooltip(
                    message,
                    <button type="button">Hover me</button>
                )
            );
            const button = screen.getByRole('button', { name: 'Hover me' });
            await user.hover(button);

            // Expected Result
            expect(await screen.findByText(message)).toBeDefined();
        });
    });
});
