// React
import { useParams } from "react-router-dom";

// Third Party
import { useTranslation } from "react-i18next";

import { fetchAllianceDetails } from "@/Api/ApiCalls";
import { queryKeys } from "@/Api/query";
import DetailsModal from "@/Components/Ledger/DetailsModal";
import { useAllianceLedger } from "@/Components/Ledger/Hooks";
import LedgerNavButton from "@/Components/Ledger/LedgerNavButton";
import LedgerView from "@/Components/Ledger/LedgerView";
import { useDateFilter } from "@/Hooks/useDateFilter";
import { useDetailsState } from "@/Hooks/useLedgerState";
import { useUserData } from "@/Hooks/useUserData";
import { corporationRows } from "@/Utils/ledger";

export interface AllianceLedgerProps {
  allianceIdOverride?: number;
  onBack?: () => void;
}

function AllianceLedger({ allianceIdOverride, onBack }: AllianceLedgerProps = {}) {
  const { t } = useTranslation();
  const params = useParams();
  const allianceId = allianceIdOverride ?? Number(params.allianceId);
  const { filters } = useDateFilter();
  const { entityId, section, openDetails, closeDetails } = useDetailsState();

  const { data: userData } = useUserData();
  const { data, isLoading, isFetching, error } = useAllianceLedger(allianceId, filters);

  return (
    <LedgerView
      title={
        data ? `${t("Alliance Ledger")} - ${data.owner.character_name}` : t("Alliance Ledger")
      }
      nameLabel={t("Corporation")}
      rows={corporationRows(data, userData?.user.corporation_id)}
      billboard={data?.billboard}
      years={data?.years ?? []}
      isLoading={isLoading}
      isFetching={isFetching}
      error={error}
      filterExtras={<LedgerNavButton onBack={onBack} />}
      onDetails={openDetails}
      onOwnerDetails={() => openDetails(allianceId, "summary")}
    >
      <DetailsModal
        entityId={entityId}
        title={t("Alliance Ledger Details")}
        queryKey={queryKeys.AllianceDetails(allianceId, entityId ?? 0, filters, section)}
        queryFn={() => fetchAllianceDetails(allianceId, entityId ?? 0, filters, section)}
        onHide={closeDetails}
      />
    </LedgerView>
  );
}

export default AllianceLedger;
