// React
import type React from "react";
import { Link } from "react-router-dom";

// Third Party
import { BookOpen, Globe } from "lucide-react";
import { Badge, Card } from "react-bootstrap";
import { useTranslation } from "react-i18next";

// AA Ledger
import type { LedgerOverviewOwnerSchema } from "@/Api/schema";
import { OwnerPortrait } from "@/Components/Base/OwnerPortrait";

export interface OverviewOwnerCardProps {
  owner: LedgerOverviewOwnerSchema;
}

const getTypeBadgeVariant = (type: string) => {
  switch (type) {
    case "character":
      return "info";
    case "corporation":
      return "primary";
    case "alliance":
      return "success";
    default:
      return "secondary";
  }
};

export const OverviewOwnerCard: React.FC<OverviewOwnerCardProps> = ({ owner }) => {
  const { t } = useTranslation();

  return (
    <Card className="h-100 bg-dark border-secondary shadow-sm">
      <Card.Body className="d-flex flex-column justify-content-between p-3 bg-body rounded">
        <div>
          <div className="d-flex align-items-center gap-3 mb-3">
            <OwnerPortrait
              src={owner.portrait_url}
              alt={owner.name}
              type={owner.type}
              bordered
            />
            <div className="overflow-hidden">
              <h5 className="mb-0 text-truncate text-light">{owner.name}</h5>
              {owner.subtitle && (
                <div className="small text-muted text-truncate mt-0.5">
                  {owner.subtitle}
                </div>
              )}
              <div className="d-flex align-items-center gap-2 mt-1">
                <Badge
                  bg={getTypeBadgeVariant(owner.type)}
                >
                  {owner.type_display}
                </Badge>
                {owner.has_planetary && (
                  <Badge
                    bg="dark"
                    className="border border-secondary text-info d-inline-flex align-items-center gap-1"
                  >
                    <Globe size={11} />
                    {t("Planetary")}
                  </Badge>
                )}
              </div>
            </div>
          </div>
        </div>

        <div className="d-flex flex-wrap gap-2 pt-2 border-top border-secondary">
          {/* Primary Ledger Button */}
          <Link
            to={`${owner.type}/${owner.id}/`}
            className="btn btn-sm btn-primary flex-fill d-flex align-items-center justify-content-center gap-1"
          >
            <BookOpen size={14} />
            {t("Ledger")}
          </Link>

          {/* Character-specific View Planetary button */}
          {owner.type === "character" && (
            <Link
              to={`planetary/${owner.id}/`}
              className="btn btn-sm btn-secondary flex-fill d-flex align-items-center justify-content-center gap-1"
            >
              <Globe size={14} />
              {t("View Planetary")}
            </Link>
          )}
        </div>
      </Card.Body>
    </Card>
  );
};

export default OverviewOwnerCard;
