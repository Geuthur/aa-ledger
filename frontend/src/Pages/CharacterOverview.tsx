// Third Party
import { useQuery } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";

import { fetchCharacterOverview } from "@/Api/ApiCalls";
import { queryKeys } from "@/Api/query";
import OverviewPage from "@/Components/Overview/OverviewPage";
import { characterImageUrl } from "@/Utils/eveOnline";

function CharacterOverview() {
  const { t } = useTranslation();
  const { data, isLoading, error } = useQuery({
    queryKey: queryKeys.CharacterOverview,
    queryFn: fetchCharacterOverview,
  });

  return (
    <OverviewPage
      title={t("Character Overview")}
      nameLabel={t("Character")}
      subtitleLabel={t("Corporation")}
      isLoading={isLoading}
      error={error}
      items={(data ?? []).map((item) => ({
        id: item.character_id,
        name: item.character_name,
        subtitle: item.corporation_name,
        icon: characterImageUrl(item.character_id, 64),
        to: `/ledger/character/${item.character_id}/`,
      }))}
    />
  );
}

export default CharacterOverview;
