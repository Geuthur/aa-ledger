// React
import type React from "react";
import { Link } from "react-router-dom";

// Third Party
import { ArrowLeft } from "lucide-react";
import { Button } from "react-bootstrap";
import { useTranslation } from "react-i18next";

export interface LedgerNavButtonProps {
  /** Set when the ledger is opened from the Administration; shows a back button instead of the overview link. */
  onBack?: () => void;
}

/** Navigation of a ledger page: back to the Administration, or to the overview. */
export const LedgerNavButton: React.FC<LedgerNavButtonProps> = ({ onBack }) => {
  const { t } = useTranslation();

  if (onBack) {
    return (
      <Button
        variant="secondary"
        size="sm"
        onClick={onBack}
        className="d-flex align-items-center gap-1"
        data-testid="back-to-administration-btn"
      >
        <ArrowLeft size={16} />
        {t("Back to Administration Overview")}
      </Button>
    );
  }

  return (
    <Link className="btn btn-secondary" to="/ledger/">
      {t("Overview")}
    </Link>
  );
};

export default LedgerNavButton;
