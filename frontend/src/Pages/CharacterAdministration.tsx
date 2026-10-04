// React
import { useParams } from "react-router";

// Third Party
import { useQuery } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";

import { deleteCharacter, fetchCharacterAdministration } from "@/Api/ApiCalls";
import { queryKeys } from "@/Api/query";
import AdministrationView from "@/Components/Administration/AdministrationView";

function CharacterAdministration() {
  const { t } = useTranslation();
  const characterId = Number(useParams().characterId);
  const queryKey = queryKeys.CharacterAdministration(characterId);

  const { data, isLoading, error } = useQuery({
    queryKey,
    queryFn: () => fetchCharacterAdministration(characterId),
  });

  return (
    <AdministrationView
      title={t("Character Administration")}
      entryLabel={t("Character")}
      data={data}
      isLoading={isLoading}
      error={error}
      queryKey={queryKey}
      ledgerPath={(ownerId) => `/ledger/character/${ownerId}/`}
      onDelete={deleteCharacter}
    />
  );
}

export default CharacterAdministration;
