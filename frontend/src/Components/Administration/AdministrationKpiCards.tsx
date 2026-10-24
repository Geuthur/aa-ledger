// React
import type React from "react";

// Third Party
import { AlertTriangle, Building2, Shield, User } from "lucide-react";
import { Card, Col, Row } from "react-bootstrap";
import { useTranslation } from "react-i18next";

export interface AdministrationMetrics {
  total: number;
  characters: number;
  corporations: number;
  alliances?: number;
  issues: number;
}

export interface AdministrationKpiCardsProps {
  metrics: AdministrationMetrics;
}

export const AdministrationKpiCards: React.FC<AdministrationKpiCardsProps> = ({ metrics }) => {
  const { t } = useTranslation();

  return (
    <Row className="g-3 mt-1 mb-3">
      <Col xs={12} sm={6} md={3}>
        <Card className="bg-dark-body border-secondary h-100 shadow-sm">
          <Card.Body className="p-3 d-flex align-items-center justify-content-between">
            <div>
              <span className="text-muted small fw-semibold">{t("Total Owners")}</span>
              <h4 className="mb-0 text-light fw-bold">{metrics.total}</h4>
            </div>
            <div className="p-2 rounded-3 bg-secondary bg-opacity-25 text-light">
              <Shield size={24} />
            </div>
          </Card.Body>
        </Card>
      </Col>

      <Col xs={12} sm={6} md={3}>
        <Card className="bg-dark-body border-secondary h-100 shadow-sm">
          <Card.Body className="p-3 d-flex align-items-center justify-content-between">
            <div>
              <span className="text-muted small fw-semibold">{t("Characters")}</span>
              <h4 className="mb-0 text-primary fw-bold">{metrics.characters}</h4>
            </div>
            <div className="p-2 rounded-3 bg-primary bg-opacity-10 text-primary">
              <User size={24} />
            </div>
          </Card.Body>
        </Card>
      </Col>

      <Col xs={12} sm={6} md={3}>
        <Card className="bg-dark-body border-secondary h-100 shadow-sm">
          <Card.Body className="p-3 d-flex align-items-center justify-content-between">
            <div>
              <span className="text-muted small fw-semibold">{t("Corporations")}</span>
              <h4 className="mb-0 text-secondary fw-bold">{metrics.corporations}</h4>
            </div>
            <div className="p-2 rounded-3 bg-secondary bg-opacity-10 text-secondary">
              <Building2 size={24} />
            </div>
          </Card.Body>
        </Card>
      </Col>

      <Col xs={12} sm={6} md={3}>
        <Card className="bg-dark-body border-secondary h-100 shadow-sm">
          <Card.Body className="p-3 d-flex align-items-center justify-content-between">
            <div>
              <span className="text-muted small fw-semibold">{t("Sync Issues")}</span>
              <h4
                className={`mb-0 fw-bold ${metrics.issues > 0 ? "text-danger" : "text-success"
                  }`}
              >
                {metrics.issues}
              </h4>
            </div>
            <div
              className={`p-2 rounded-3 ${metrics.issues > 0
                ? "bg-danger bg-opacity-10 text-danger"
                : "bg-success bg-opacity-10 text-success"
                }`}
            >
              {metrics.issues > 0 ? <AlertTriangle size={24} /> : <Shield size={24} />}
            </div>
          </Card.Body>
        </Card>
      </Col>
    </Row>
  );
};

export default AdministrationKpiCards;
