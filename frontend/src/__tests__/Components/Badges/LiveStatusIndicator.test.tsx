// Third Party
import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

// Voices of War
import { LiveStatusIndicator } from '@/Components/Badges/LiveStatusIndicator';

vi.mock('react-i18next', () => ({
    useTranslation: () => ({
        t: (key: string) => key,
    }),
}));

describe('LiveStatusIndicator', () => {
    it('should render green dot by default when idle', () => {
        // Test Data
        const { container } = render(<LiveStatusIndicator dataUpdatedAt={Date.now()} />);

        // Test Action
        const greenDot = container.querySelector('.aa-status-dot-ready');

        // Expected Result
        expect(greenDot).toBeTruthy();
    });

    it('should render amber pulsing dot when isLoading is true', () => {
        // Test Data
        const { container } = render(<LiveStatusIndicator isLoading={true} />);

        // Test Action
        const amberDot = container.querySelector('.aa-status-dot-busy');

        // Expected Result
        expect(amberDot).toBeTruthy();
    });

    it('should render red dot when isError is true', () => {
        // Test Data
        const { container } = render(<LiveStatusIndicator isError={true} />);

        // Test Action
        const redDot = container.querySelector('.aa-status-dot-error');

        // Expected Result
        expect(redDot).toBeTruthy();
    });

    it('should display error timestamp text when showTimestamp and isError are true', () => {
        // Test Data
        render(<LiveStatusIndicator isError={true} showTimestamp={true} />);

        // Test Action
        const errorText = screen.getByText(/Fehler/i);

        // Expected Result
        expect(errorText).toBeTruthy();
        expect(errorText.className).toContain('aa-status-text-error');
    });

    it('should render children when passed', () => {
        // Test Data
        render(
            <LiveStatusIndicator isError={true}>
                <span>COMBAT LOG</span>
            </LiveStatusIndicator>
        );

        // Test Action
        const label = screen.getByText('COMBAT LOG');

        // Expected Result
        expect(label).toBeTruthy();
    });
});
