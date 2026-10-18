// React
import type { ReactNode } from 'react';

// Third Party
import { Card } from 'react-bootstrap';

export interface BaseSectionHeaderProps {
    name?: string;
    children?: ReactNode;
}

function BaseSectionHeader({ name = "Header", children }: BaseSectionHeaderProps) {
    return (
        <Card className="aa-panel lg-header" aria-labelledby="section-heading">
            <Card.Body className="d-flex flex-wrap align-items-center justify-content-between p-0">
                <h3 id="section-heading" className="aa-section-title mb-0">{name}</h3>
                {children && <div className="lg-toolbar">{children}</div>}
            </Card.Body>
        </Card>
    );
};

export default BaseSectionHeader;
