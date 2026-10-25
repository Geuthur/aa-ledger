// React
import { Navigate } from "react-router-dom";

// Third Party
import { useTranslation } from "react-i18next";

import ErrorLoader from "@/Components/Base/Loader/ErrorLoader";
import FetchingLoader from "@/Components/Base/Loader/FetchingLoader";
import { useUserData } from "@/Hooks/useUserData";

export interface MainCharacterRedirectProps {
  /** Route of the main character, e.g. `character` for `/ledger/character/{id}/`. */
  to: "character" | "planetary";
}

/** Sends the user to the page of their main character. */
function MainCharacterRedirect({ to }: MainCharacterRedirectProps) {
  const { t } = useTranslation();
  const { data, isLoading, error } = useUserData();

  if (isLoading) return <FetchingLoader message={t("Loading…")} />;
  if (error || !data || !data.user.character_id) {
    return (
      <ErrorLoader
        title={t("Error")}
        message={error?.message ?? t("No main character found.")}
      />
    );
  }
  return <Navigate to={`/ledger/${to}/${data.user.character_id}/`} replace />;
}

export default MainCharacterRedirect;
