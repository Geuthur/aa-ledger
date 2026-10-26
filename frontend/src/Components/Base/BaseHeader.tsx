// React
import type { ReactNode } from "react";

// Third Party
import { Card } from "react-bootstrap";

export interface BaseSectionHeaderProps {
    name?: string;
    children?: ReactNode;
}

function BaseSectionHeader({ name = "Header", children }: BaseSectionHeaderProps) {
    return (
        <Card className="bg-dark border-secondary mb-3 shadow-sm">
            <Card.Body className="d-flex flex-wrap align-items-center justify-content-between gap-2 p-3">
                <h3 id="section-heading" className="h4 mb-0 fw-bold">{name}</h3>
                {children && <div className="d-flex flex-wrap align-items-center gap-2">{children}</div>}
            </Card.Body>
        </Card>
    );
}

export default BaseSectionHeader;
