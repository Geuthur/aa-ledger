// React
import { MemoryRouter } from 'react-router';

// Third Party
import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

// AA Example
import AuthRightMenu from '@/Menu/AuthRightMenu';

vi.mock('react-i18next', async (importOriginal) => {
    const actual = await importOriginal<typeof import('react-i18next')>();
    return {
        ...actual,
        useTranslation: () => ({
            t: (key: string) => key,
        }),
    };
});

describe('AuthRightMenu', () => {
    it('should render internal navigation links for right menu', () => {
        // Test Data
        const testData = [
            { name: 'Admin', link: 'admin' },
        ];

        // Test Action
        render(
            <MemoryRouter initialEntries={['/ledger/']}>
                <AuthRightMenu data={testData} isLoading={false} error={false} />
            </MemoryRouter>
        );

        // Expected Result
        const adminLink = screen.getByText('Admin');
        expect(adminLink).toBeDefined();
        expect(adminLink.getAttribute('href')).toBe('/ledger/admin/');
    });

    it('should render external links in right menu', () => {
        // Test Data
        const testData = [
            { name: 'GitHub Issues', link: 'https://github.com/example/issues', is_external: true },
        ];

        // Test Action
        render(
            <MemoryRouter>
                <AuthRightMenu data={testData} isLoading={false} error={false} />
            </MemoryRouter>
        );

        // Expected Result
        const externalLink = screen.getByText('GitHub Issues');
        expect(externalLink).toBeDefined();
        expect(externalLink.getAttribute('href')).toBe('https://github.com/example/issues');
    });

    it('should filter out items without links', () => {
        // Test Data
        const testData = [
            { name: 'Category Only' },
        ];

        // Test Action
        const { container } = render(
            <MemoryRouter>
                <AuthRightMenu data={testData} isLoading={false} error={false} />
            </MemoryRouter>
        );

        // Expected Result
        expect(container.querySelectorAll('li')).toHaveLength(0);
    });
});
