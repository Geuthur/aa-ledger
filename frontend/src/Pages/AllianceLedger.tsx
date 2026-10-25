// React
import { Link, useParams } from "react-router-dom";

// Third Party
import { keepPreviousData, useQuery } from "@tanstack/react-query";
import { ArrowLeft } from "lucide-react";
import { Button } from "react-bootstrap";
import { useTranslation } from "react-i18next";

import { fetchAllianceDetails, fetchAllianceLedger, loadUserData } from "@/Api/ApiCalls";
import { queryKeys } from "@/Api/query";
import DetailsModal from "@/Components/Ledger/DetailsModal";
import LedgerView from "@/Components/Ledger/LedgerView";
import { useDateFilter } from "@/Hooks/useDateFilter";
import { useDetailsState } from "@/Hooks/useLedgerState";
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

  const { data: userData } = useQuery({
    queryKey: queryKeys.User,
    queryFn: loadUserData,
  });

  const { data, isLoading, isFetching, error } = useQuery({
    queryKey: queryKeys.AllianceLedger(allianceId, filters),
    queryFn: () => fetchAllianceLedger(allianceId, filters),
    placeholderData: keepPreviousData,
    enabled: Boolean(allianceId),
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
        onBack ? (
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
        ) : (
          <Link className="btn btn-secondary" to="/ledger/">
            {t("Overview")}
          </Link>
        )
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
