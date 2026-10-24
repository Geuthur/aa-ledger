// React
import type React from "react";

// Third Party
import {
  Building2,
  ChevronDown,
  ChevronUp,
  RefreshCw,
  User,
} from "lucide-react";
import { Button, Card, Col, Form, Row, Spinner } from "react-bootstrap";
import { useTranslation } from "react-i18next";

// Styles
import styles from "@/Styles/modules/Administration.module.css";

export interface AdministrationTaskPanelProps {
  showTaskPanel: boolean;
  onToggleTaskPanel: () => void;
  forceRefreshGlobal: boolean;
  onToggleForceRefresh: (checked: boolean) => void;
  isPending: boolean;
  onUpdateTarget: (target: "characters" | "corporations") => void;
}

export const AdministrationTaskPanel: React.FC<AdministrationTaskPanelProps> = ({
  showTaskPanel,
  onToggleTaskPanel,
  forceRefreshGlobal,
  onToggleForceRefresh,
  isPending,
  onUpdateTarget,
}) => {
  const { t } = useTranslation();

  return (
    <Card className="bg-dark border-secondary mb-4 shadow-sm">
      <Card.Header
        className={`border-secondary d-flex align-items-center justify-content-between py-2 ${styles.cursorPointer}`}
        onClick={onToggleTaskPanel}
      >
        <div className="d-flex align-items-center gap-2">
          <RefreshCw size={16} className="text-primary" />
          <span className="fw-semibold text-light">
            {t("Global Task Administration")}
          </span>
        </div>
        <Button
          variant="link"
          size="sm"
          className="p-0 text-muted"
          aria-label={t("Toggle Task Administration")}
          data-testid="toggle-task-panel"
          onClick={(e) => {
            e.stopPropagation();
            onToggleTaskPanel();
          }}
        >
          {showTaskPanel ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
        </Button>
      </Card.Header>

      {showTaskPanel && (
        <Card.Body className="p-3">
          <Form.Group className="mb-3">
            <Form.Check
              type="switch"
              id="global-force-refresh"
              label={<span className="small text-muted">{t("Force Refresh ESI")}</span>}
              checked={forceRefreshGlobal}
              onChange={(e) => onToggleForceRefresh(e.target.checked)}
              data-testid="force-refresh-switch"
            />
          </Form.Group>

          <Row className="g-3">
            <Col md={6}>
              <Card className="bg-dark border-secondary h-100">
                <Card.Header className="border-secondary py-2">
                  <h6 className="mb-0 text-light">{t("Characters")}</h6>
                </Card.Header>
                <Card.Body className="d-flex flex-column justify-content-between p-3 bg-dark">
                  <p className="text-muted small">
                    {t("Queue background tasks to synchronize all active characters.")}
                  </p>
                  <Button
                    variant="primary"
                    size="sm"
                    disabled={isPending}
                    onClick={() => onUpdateTarget("characters")}
                    className="w-100 d-flex align-items-center justify-content-center gap-1"
                    data-testid="update-all-characters-btn"
                  >
                    {isPending ? (
                      <Spinner size="sm" animation="border" />
                    ) : (
                      <User size={14} />
                    )}
                    {t("Update All Characters")}
                  </Button>
                </Card.Body>
              </Card>
            </Col>

            <Col md={6}>
              <Card className="bg-dark border-secondary h-100">
                <Card.Header className="border-secondary py-2">
                  <h6 className="mb-0 text-light">{t("Corporations")}</h6>
                </Card.Header>
                <Card.Body className="d-flex flex-column justify-content-between p-3 bg-dark">
                  <p className="text-muted small">
                    {t("Queue background tasks to synchronize all active corporations.")}
                  </p>
                  <Button
                    variant="primary"
                    size="sm"
                    disabled={isPending}
                    onClick={() => onUpdateTarget("corporations")}
                    className="w-100 d-flex align-items-center justify-content-center gap-1"
                    data-testid="update-all-corporations-btn"
                  >
                    {isPending ? (
                      <Spinner size="sm" animation="border" />
                    ) : (
                      <Building2 size={14} />
                    )}
                    {t("Update All Corporations")}
                  </Button>
                </Card.Body>
              </Card>
            </Col>
          </Row>
        </Card.Body>
      )}
    </Card>
  );
};

export default AdministrationTaskPanel;
