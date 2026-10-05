// React
import { Link, useParams } from "react-router";

// Third Party
import { keepPreviousData, useQuery } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";

import { fetchCharacterDetails, fetchCharacterLedger } from "@/Api/ApiCalls";
import { queryKeys } from "@/Api/query";
import DetailsModal from "@/Components/Ledger/DetailsModal";
import LedgerView from "@/Components/Ledger/LedgerView";
import { useDateFilter } from "@/Hooks/useDateFilter";
import { useDetailsState } from "@/Hooks/useLedgerState";
import { characterRows } from "@/Utils/ledger";

function CharacterLedger() {
  const { t } = useTranslation();
  const characterId = Number(useParams().characterId);
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
          <Link className="aa-btn aa-btn-primary" to="/ledger/character/">
            {t("Overview")}
          </Link>
          <Link className="aa-btn aa-btn-primary" to={`/ledger/character/${characterId}/administration/`}>
            {t("Administration")}
          </Link>
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
