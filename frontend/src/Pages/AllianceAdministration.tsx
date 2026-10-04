// React
import { useParams } from "react-router";

// Third Party
import { useQuery } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";

import { fetchAllianceAdministration } from "@/Api/ApiCalls";
import { queryKeys } from "@/Api/query";
import AdministrationView from "@/Components/Administration/AdministrationView";

function AllianceAdministration() {
  const { t } = useTranslation();
  const allianceId = Number(useParams().allianceId);
  const queryKey = queryKeys.AllianceAdministration(allianceId);

  const { data, isLoading, error } = useQuery({
    queryKey,
    queryFn: () => fetchAllianceAdministration(allianceId),
  });

  return (
    <AdministrationView
      title={t("Alliance Administration")}
      entryLabel={t("Corporation")}
      data={data}
      isLoading={isLoading}
      error={error}
      queryKey={queryKey}
      ledgerPath={(ownerId) => `/ledger/corporation/${ownerId}/`}
    />
  );
}

export default AllianceAdministration;
