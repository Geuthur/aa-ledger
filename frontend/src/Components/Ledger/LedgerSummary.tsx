// Third Party
import { Info } from "lucide-react";
import { Col, Row } from "react-bootstrap";
import { useTranslation } from "react-i18next";

import { renderTooltip } from "@/Components/Tables/BaseTable/tableHelper";
import { amountClass, formatIsk } from "@/Utils/ledger";
import type { LedgerTotals } from "@/Utils/ledger";

export interface LedgerSummaryProps {
  totals: LedgerTotals;
  showMining?: boolean;
  /** Opens the category breakdown of the whole owner. */
  onDetails?: () => void;
}

function LedgerSummary({ totals, showMining = false, onDetails }: LedgerSummaryProps) {
  const { t } = useTranslation();

  const items = [
    { label: t("Bounty"), value: totals.bounty },
    { label: t("ESS"), value: totals.ess },
    ...(showMining ? [{ label: t("Mining"), value: totals.mining ?? 0, mining: true }] : []),
    { label: t("Miscellaneous"), value: totals.miscellaneous },
    { label: t("Costs"), value: totals.costs },
    { label: t("Total"), value: totals.total },
  ];

  return (
    <Row className="g-2 align-items-stretch" aria-label={t("Summary")}>
      {items.map((item) => (
        <Col key={item.label} xs={6} md>
          <div className="aa-panel h-100">
            <div className="text-muted small">{item.label}</div>
            <div className={`fw-bold ${amountClass(item.value, "mining" in item)}`}>
              {formatIsk(item.value)}
            </div>
          </div>
        </Col>
      ))}
      {onDetails && (
        <Col xs="auto" className="d-flex align-items-center">
          {renderTooltip(
            t("View Details"),
            <button
              type="button"
              className="lg-btn lg-btn-primary"
              aria-label={t("View Details")}
              onClick={onDetails}
            >
              <Info size={16} />
            </button>,
          )}
        </Col>
      )}
    </Row>
  );
}

export default LedgerSummary;
