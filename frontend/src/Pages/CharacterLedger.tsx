// React
import { useParams } from "react-router-dom";

// Third Party
import { useTranslation } from "react-i18next";

import { fetchCharacterDetails } from "@/Api/ApiCalls";
import { queryKeys } from "@/Api/query";
import DetailsModal from "@/Components/Ledger/DetailsModal";
import { useCharacterLedger } from "@/Components/Ledger/Hooks";
import LedgerNavButton from "@/Components/Ledger/LedgerNavButton";
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

  const { data, isLoading, isFetching, error } = useCharacterLedger(characterId, filters);

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
          <LedgerNavButton onBack={onBack} />
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
