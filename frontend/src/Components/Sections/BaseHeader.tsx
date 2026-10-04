// React
import type { ReactNode } from 'react';

export interface BaseSectionHeaderProps {
    name?: string;
    children?: ReactNode;
}

function BaseSectionHeader({ name = "Header", children }: BaseSectionHeaderProps) {
    return (
        <section className="aa-panel lg-header" aria-labelledby="section-heading">
            <h3 id="section-heading" className="aa-section-title mb-0">{name}</h3>
            {children && <div className="lg-toolbar">{children}</div>}
        </section>
    );
};

export default BaseSectionHeader;
