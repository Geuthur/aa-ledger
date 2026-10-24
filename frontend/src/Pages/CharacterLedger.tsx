// React
import { Link, useParams } from "react-router";

// Third Party
import { keepPreviousData, useQuery } from "@tanstack/react-query";
import { ArrowLeft } from "lucide-react";
import { Button } from "react-bootstrap";
import { useTranslation } from "react-i18next";

import { fetchCharacterDetails, fetchCharacterLedger } from "@/Api/ApiCalls";
import { queryKeys } from "@/Api/query";
import DetailsModal from "@/Components/Ledger/DetailsModal";
import LedgerView from "@/Components/Ledger/LedgerView";
import { useDateFilter } from "@/Hooks/useDateFilter";
import { useDetailsState } from "@/Hooks/useLedgerState";
import { characterRows } from "@/Utils/ledger";

export interface CharacterLedgerProps {
  characterIdOverride?: number;
  onBack?: () => void;
}

function CharacterLedger({ characterIdOverride, onBack }: CharacterLedgerProps = {}) {
  const { t } = useTranslation();
  const params = useParams();
  const characterId = characterIdOverride ?? Number(params.characterId);
  const { filters } = useDateFilter();
  const { entityId, section, openDetails, closeDetails } = useDetailsState();

  const { data, isLoading, isFetching, error } = useQuery({
    queryKey: queryKeys.CharacterLedger(characterId, filters),
    queryFn: () => fetchCharacterLedger(characterId, filters),
    placeholderData: keepPreviousData,
  });

  return (
    <LedgerView
      title={data ? `${t("Character Ledger")} - ${data.owner.character_name}` : t("Character Ledger")}
      nameLabel={t("Character")}
      rows={characterRows(data)}
      showMining
      billboard={data?.billboard}
      years={data?.years ?? []}
      isLoading={isLoading}
      isFetching={isFetching}
      error={error}
      filterExtras={
        <>
          {onBack ? (
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
            <>
              <Link className="btn btn-secondary" to="/ledger/">
                {t("Overview")}
              </Link>
            </>
          )}
        </>
      }
      onDetails={openDetails}
      onOwnerDetails={() => openDetails(characterId, "summary")}
    >
      <DetailsModal
        entityId={entityId}
        title={t("Character Ledger Details")}
        queryKey={queryKeys.CharacterDetails(entityId ?? 0, filters, section)}
        queryFn={() => fetchCharacterDetails(entityId ?? 0, filters, section)}
        onHide={closeDetails}
      />
    </LedgerView>
  );
}

export default CharacterLedger;
