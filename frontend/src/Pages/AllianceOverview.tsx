// Third Party
import { useQuery } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";

import { fetchAllianceOverview } from "@/Api/ApiCalls";
import { queryKeys } from "@/Api/query";
import OverviewPage from "@/Components/Overview/OverviewPage";
import { allianceImageUrl } from "@/Utils/eveOnline";

function AllianceOverview() {
  const { t } = useTranslation();
  const { data, isLoading, error } = useQuery({
    queryKey: queryKeys.AllianceOverview,
    queryFn: fetchAllianceOverview,
  });

  return (
    <OverviewPage
      title={t("Alliance Overview")}
      nameLabel={t("Alliance")}
      isLoading={isLoading}
      error={error}
      items={(data ?? []).map((item) => ({
        id: item.alliance_id,
        name: item.alliance_name,
        icon: allianceImageUrl(item.alliance_id, 64),
        to: `/ledger/alliance/${item.alliance_id}/`,
      }))}
    />
  );
}

export default AllianceOverview;
