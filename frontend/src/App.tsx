// React
import React from "react"
import {  BrowserRouter, Navigate, Route, Routes } from "react-router-dom"

// Third Party
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import i18n from "i18next";
import Backend from "i18next-http-backend";
import { NuqsAdapter } from "nuqs/adapters/react-router/v8";
import { initReactI18next } from "react-i18next";

import { ErrorPage } from "@/Pages/404";
import Admin from "@/Pages/Admin";
import AllianceAdministration from "@/Pages/AllianceAdministration";
import AllianceLedger from "@/Pages/AllianceLedger";
import AllianceOverview from "@/Pages/AllianceOverview";
import AuthBase from "@/Pages/Base";
import CharacterAdministration from "@/Pages/CharacterAdministration";
import CharacterLedger from "@/Pages/CharacterLedger";
import CharacterOverview from "@/Pages/CharacterOverview";
import CorporationAdministration from "@/Pages/CorporationAdministration";
import CorporationLedger from "@/Pages/CorporationLedger";
import CorporationOverview from "@/Pages/CorporationOverview";
import MainCharacterRedirect from "@/Pages/MainCharacterRedirect";
import Planetary from "@/Pages/Planetary";
import PlanetaryOverview from "@/Pages/PlanetaryOverview";
import Settings from "@/Pages/Settings";

const queryClient = new QueryClient();
export const AppName = "aa-ledger";
export const ProjectName = "ledger";

// Read language directly from Django's LANGUAGE_CODE (set as lang="..." on root div)
const djangoLanguage = typeof document !== "undefined" ? document.getElementById(`${AppName}-root`)?.getAttribute("lang") ?? "en" : "en";

i18n
  .use(Backend)
  .use(initReactI18next)
  .init({
    lng: djangoLanguage,
    fallbackLng: "en",
    keySeparator: false,
    nsSeparator: false,
    interpolation: {
      escapeValue: false, // react already safes from xss => https://www.i18next.com/translation-function/interpolation#unescape
    },
    react: {
      useSuspense: false, //   <---- this will do the magic
    },
    backend: {
      loadPath: `/static/${ProjectName}/i18n/{{lng}}/{{ns}}.json`,
    },
  });

function App() {
  return (
    <React.StrictMode>
      <QueryClientProvider client={queryClient}>
        <BrowserRouter>
          <NuqsAdapter>
            <Routes>
              <Route path={`/${ProjectName}/`} element={<AuthBase />}>
                <Route index element={<MainCharacterRedirect to="character" />} />
                <Route path="character/" element={<CharacterOverview />} />
                <Route path="character/:characterId/" element={<CharacterLedger />} />
                <Route
                  path="character/:characterId/administration/"
                  element={<CharacterAdministration />}
                />
                <Route path="planetary/" element={<MainCharacterRedirect to="planetary" />} />
                <Route path="planetary/overview/" element={<PlanetaryOverview />} />
                <Route path="planetary/:characterId/" element={<Planetary />} />
                <Route path="corporation/" element={<CorporationOverview />} />
                <Route path="corporation/:corporationId/" element={<CorporationLedger />} />
                <Route
                  path="corporation/:corporationId/administration/"
                  element={<CorporationAdministration />}
                />
                <Route path="alliance/" element={<AllianceOverview />} />
                <Route path="alliance/:allianceId/" element={<AllianceLedger />} />
                <Route
                  path="alliance/:allianceId/administration/"
                  element={<AllianceAdministration />}
                />
                <Route path="settings/" element={<Settings />} />
                <Route path="admin/" element={<Admin />} />
                <Route path="*" element={<ErrorPage />} />
              </Route>
              <Route path="*" element={<Navigate to={`/${ProjectName}/`} replace />} />
            </Routes>
          </NuqsAdapter>
        </BrowserRouter>
      </QueryClientProvider>
    </React.StrictMode>
  )
}

export default App
