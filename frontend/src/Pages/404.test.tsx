// Third Party
import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

// AA Example
import { ErrorPage } from '@/Pages/404';

vi.mock('react-i18next', () => ({
    useTranslation: () => ({
        t: (key: string) => key,
    }),
    withTranslation: () => (Component: unknown) => Component,
}));

describe('ErrorPage (404)', () => {
    it('should render 404 title and message', () => {
        // Test Data & Test Action
        render(<ErrorPage />);

        // Expected Result
        expect(screen.getByText('Error 404')).toBeDefined();
        expect(screen.getByText('The page you are looking for does not exist.')).toBeDefined();
    });
});
