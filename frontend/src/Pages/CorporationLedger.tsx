// React
import { useParams } from "react-router-dom";

// Third Party
import { useTranslation } from "react-i18next";

import { fetchCorporationDetails } from "@/Api/ApiCalls";
import { queryKeys } from "@/Api/query";
import type { CorporationFilterParams } from "@/Api/schema";
import DetailsModal from "@/Components/Ledger/DetailsModal";
import { useCorporationLedger } from "@/Components/Ledger/Hooks";
import LedgerNavButton from "@/Components/Ledger/LedgerNavButton";
import LedgerView from "@/Components/Ledger/LedgerView";
import { useDateFilter } from "@/Hooks/useDateFilter";
import { useDetailsState, useDivisionFilter } from "@/Hooks/useLedgerState";
import { entityRows } from "@/Utils/ledger";

export interface CorporationLedgerProps {
  corporationIdOverride?: number;
  onBack?: () => void;
}

function CorporationLedger({ corporationIdOverride, onBack }: CorporationLedgerProps = {}) {
  const { t } = useTranslation();
  const params = useParams();
  const corporationId = corporationIdOverride ?? Number(params.corporationId);
  const { filters: dateFilters } = useDateFilter();
  const [division, setDivision] = useDivisionFilter();
  const { entityId, section, openDetails, closeDetails } = useDetailsState();

  const filters: CorporationFilterParams = {
    ...dateFilters,
    ...(division !== null ? { division_id: division } : {}),
  };

  const { data, isLoading, isFetching, error } = useCorporationLedger(corporationId, filters);

  return (
    <LedgerView
      title={
        data ? `${t("Corporation Ledger")} - ${data.owner.character_name}` : t("Corporation Ledger")
      }
      nameLabel={t("Entity")}
      rows={entityRows(data)}
      billboard={data?.billboard}
      years={data?.years ?? []}
      isLoading={isLoading}
      isFetching={isFetching}
      error={error}
      filterExtras={
        <>
          <select
            aria-label={t("Division")}
            className="lg-select"
            value={division ?? ""}
            onChange={(event) => setDivision(event.target.value ? Number(event.target.value) : null)}
          >
            <option value="">{t("All Divisions")}</option>
            {(data?.divisions ?? []).map((item) => (
              <option key={item.division_id} value={item.division_id}>
                {item.name}
              </option>
            ))}
          </select>
          <LedgerNavButton onBack={onBack} />
        </>
      }
      onDetails={openDetails}
      onOwnerDetails={() => openDetails(corporationId, "summary")}
    >
      <DetailsModal
        entityId={entityId}
        title={t("Corporation Ledger Details")}
        queryKey={queryKeys.CorporationDetails(corporationId, entityId ?? 0, filters, section)}
        queryFn={() => fetchCorporationDetails(corporationId, entityId ?? 0, filters, section)}
        onHide={closeDetails}
      />
    </LedgerView>
  );
}

export default CorporationLedger;
