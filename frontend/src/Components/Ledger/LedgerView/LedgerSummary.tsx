// Third Party
import {
  Boxes,
  CircleHelp,
  Info,
  Pickaxe,
  Shield,
  Skull,
  TrendingDown,
  TrendingUp,
} from "lucide-react";
import { Button, Card, Col, Row } from "react-bootstrap";
import { useTranslation } from "react-i18next";

import { renderTooltip } from "@/Components/Base/BaseTable/tableHelper";
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
    {
      label: t("Bounty"),
      value: totals.bounty,
      icon: Skull,
      color: "#f43f5e",
    },
    {
      label: t("ESS"),
      value: totals.ess,
      icon: Shield,
      color: "#38bdf8",
    },
    ...(showMining
      ? [
        {
          label: t("Mining"),
          value: totals.mining ?? 0,
          mining: true,
          icon: Pickaxe,
          color: "#fbbf24",
          infoTooltip: t(
            "This is only an informational value and is not included in calculations.",
          ),
        },
      ]
      : []),
    {
      label: t("Miscellaneous"),
      value: totals.miscellaneous,
      icon: Boxes,
      color: "#c084fc",
    },
    {
      label: t("Costs"),
      value: totals.costs,
      icon: TrendingDown,
      color: "#fb7185",
    },
    {
      label: t("Total"),
      value: totals.total,
      icon: TrendingUp,
      color: totals.total >= 0 ? "#34d399" : "#fb7185",
    },
  ];

  return (
    <Row className="g-2 align-items-stretch" aria-label={t("Summary")}>
      {items.map((item) => {
        const Icon = item.icon;
        return (
          <Col key={item.label} xs={6} md>
            <Card className="bg-dark border-secondary h-100 shadow-sm">
              <Card.Body className="p-3 d-flex flex-column justify-content-between">
                <div className="d-flex justify-content-between align-items-start mb-2 gap-2">
                  <span className="small fw-semibold text-uppercase d-inline-flex align-items-center gap-1">
                    {item.label}
                    {"infoTooltip" in item && item.infoTooltip && (
                      renderTooltip(
                        item.infoTooltip,
                        <span
                          className="d-inline-flex align-items-center text-muted"
                          style={{ cursor: "help" }}
                        >
                          <CircleHelp size={14} />
                        </span>,
                      )
                    )}
                  </span>
                  <Icon color={item.color} size={24} className="flex-shrink-0" />
                </div>
                <span className={`h5 mb-0 fw-bold ${amountClass(item.value, "mining" in item)}`}>
                  {formatIsk(item.value)}
                </span>
              </Card.Body>
            </Card>
          </Col>
        );
      })}
      {onDetails && (
        <Col xs="auto" className="d-flex align-items-center">
          {renderTooltip(
            t("View Details"),
            <Button
              variant="primary"
              onClick={onDetails}
              aria-label={t("View Details")}
            >
              <Info size={16} />
            </Button>,
          )}
        </Col>
      )}
    </Row>
  );
}

export default LedgerSummary;
