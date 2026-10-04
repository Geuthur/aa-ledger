// Third Party
import { useTranslation } from "react-i18next";

import type { RefTypeAmountSchema } from "@/Api/schema";
import { formatIsk } from "@/Utils/ledger";
import { MAX_REF_TYPE_BADGES, formatRefType } from "@/Utils/refTypes";

export interface RefTypeBadgesProps {
  refTypes: RefTypeAmountSchema[];
  /** Print the amount into the badge, e.g. while searching for a reference type. */
  showAmounts?: boolean;
  /** Opens the list with all reference types, offered if there are more than the badges. */
  onShowAll: () => void;
}

/** One badge per reference type; the rest is reachable through the "more" button. */
function RefTypeBadges({ refTypes, showAmounts = false, onShowAll }: RefTypeBadgesProps) {
  const { t } = useTranslation();
  const hidden = refTypes.length - MAX_REF_TYPE_BADGES;

  return (
    <span className="d-inline-flex flex-wrap gap-1">
      {refTypes.slice(0, MAX_REF_TYPE_BADGES).map((item) => (
        <span key={item.ref_type}>
          <span className="badge bg-primary">
            {formatRefType(item.ref_type)}
            {showAmounts && `: ${formatIsk(item.amount ?? 0)}`}
          </span>
        </span>
      ))}
      {hidden > 0 && (
        <button type="button" className="badge bg-primary border-0" onClick={onShowAll}>
          {t("+{{number}} more", { number: hidden })}
        </button>
      )}
    </span>
  );
}

export default RefTypeBadges;
