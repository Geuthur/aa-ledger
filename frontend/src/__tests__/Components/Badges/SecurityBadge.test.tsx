// Third Party
import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

// AA Example
import { SecurityBadge } from '@/Components/Badges/SecurityBadge';

describe('SecurityBadge', () => {
    it('should render formatted security number with one decimal place', () => {
        // Test Data
        const sec = 0.8;

        // Test Action
        render(<SecurityBadge sec={sec} />);

        // Expected Result
        expect(screen.getByText('0.8')).toBeDefined();
    });

    it('should apply highsec colors for security >= 0.5', () => {
        // Test Data
        const sec = 1.0;

        // Test Action
        const { container } = render(<SecurityBadge sec={sec} />);
        const badge = container.querySelector('.sec-badge');

        // Expected Result
        expect(badge?.className).toContain('aa-badge-hisec');
    });

    it('should apply lowsec colors for security between 0.1 and 0.4', () => {
        // Test Data
        const sec = 0.3;

        // Test Action
        const { container } = render(<SecurityBadge sec={sec} />);
        const badge = container.querySelector('.sec-badge');

        // Expected Result
        expect(badge?.className).toContain('aa-badge-lowsec');
    });

    it('should apply nullsec colors for security <= 0.0', () => {
        // Test Data
        const sec = -0.5;

        // Test Action
        const { container } = render(<SecurityBadge sec={sec} />);
        const badge = container.querySelector('.sec-badge');

        // Expected Result
        expect(badge?.className).toContain('aa-badge-nullsec');
    });

    it('should include additional custom className when provided', () => {
        // Test Data
        const sec = 0.6;
        const customClass = 'extra-badge-style';

        // Test Action
        const { container } = render(<SecurityBadge sec={sec} className={customClass} />);
        const badge = container.querySelector('.sec-badge');

        // Expected Result
        expect(badge?.className).toContain('extra-badge-style');
    });
});
