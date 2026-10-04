// React
import { Link, useParams } from "react-router";

// Third Party
import { keepPreviousData, useQuery } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";

import { fetchAllianceDetails, fetchAllianceLedger, loadUserData } from "@/Api/ApiCalls";
import { queryKeys } from "@/Api/query";
import DetailsModal from "@/Components/Ledger/DetailsModal";
import LedgerView from "@/Components/Ledger/LedgerView";
import { useDateFilter } from "@/Hooks/useDateFilter";
import { useDetailsState } from "@/Hooks/useLedgerState";
import { corporationRows } from "@/Utils/ledger";

function AllianceLedger() {
  const { t } = useTranslation();
  const allianceId = Number(useParams().allianceId);
  const { filters } = useDateFilter();
  const { entityId, section, openDetails, closeDetails } = useDetailsState();

  const { data: userData } = useQuery({
    queryKey: queryKeys.User,
    queryFn: loadUserData,
  });

  const { data, isLoading, isFetching, error } = useQuery({
    queryKey: queryKeys.AllianceLedger(allianceId, filters),
    queryFn: () => fetchAllianceLedger(allianceId, filters),
    placeholderData: keepPreviousData,
  });

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
      filterExtras={
        <>
          <Link className="lg-btn lg-btn-secondary" to="/ledger/alliance/">
            {t("Overview")}
          </Link>
          <Link className="lg-btn lg-btn-secondary" to={`/ledger/alliance/${allianceId}/administration/`}>
            {t("Administration")}
          </Link>
        </>
      }
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
