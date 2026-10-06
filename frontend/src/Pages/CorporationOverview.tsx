// Third Party
import { useQuery } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";

import { fetchCorporationOverview } from "@/Api/ApiCalls";
import { queryKeys } from "@/Api/query";
import OverviewPage from "@/Components/Overview/OverviewPage";
import { corporationImageUrl } from "@/Utils/eveOnline";

function CorporationOverview() {
  const { t } = useTranslation();
  const { data, isLoading, error } = useQuery({
    queryKey: queryKeys.CorporationOverview,
    queryFn: fetchCorporationOverview,
  });

  return (
    <OverviewPage
      title={t("Corporation Overview")}
      nameLabel={t("Corporation")}
      isLoading={isLoading}
      error={error}
      items={(data ?? []).map((item) => ({
        id: item.corporation_id,
        name: item.corporation_name,
        icon: corporationImageUrl(item.corporation_id, 64),
        to: `/ledger/corporation/${item.corporation_id}/`,
      }))}
    />
  );
}

export default CorporationOverview;
