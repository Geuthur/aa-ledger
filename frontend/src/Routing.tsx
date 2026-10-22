// React
import React from "react"
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom"

// Third Party
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { NuqsAdapter } from "nuqs/adapters/react-router/v8";

import { ProjectName } from "@/constants";
import { ErrorPage } from "@/Pages/404";
import AllianceLedger from "@/Pages/AllianceLedger";
import AuthBase from "@/Pages/Base";
import CharacterLedger from "@/Pages/CharacterLedger";
import CorporationLedger from "@/Pages/CorporationLedger";
import MainCharacterRedirect from "@/Pages/MainCharacterRedirect";
import OverviewPage from "@/Pages/OverviewPage";
import Planetary from "@/Pages/Planetary";
import SettingsPage from "@/Pages/SettingsPage";
import SuperuserPage from "@/Pages/SuperuserPage";

const queryClient = new QueryClient();

function Routing() {
  return (
    <React.StrictMode>
      <QueryClientProvider client={queryClient}>
        <BrowserRouter>
          <NuqsAdapter>
            <Routes>
              <Route path={`/${ProjectName}/`} element={<AuthBase />}>
                <Route index element={<OverviewPage />} />
                <Route path="overview/" element={<OverviewPage />} />
                <Route path="character/" element={<MainCharacterRedirect to="character" />} />
                <Route path="character/:characterId/" element={<CharacterLedger />} />
                <Route path="planetary/" element={<MainCharacterRedirect to="planetary" />} />
                <Route path="planetary/overview/" element={<Navigate to={`/${ProjectName}/`} replace />} />
                <Route path="planetary/:characterId/" element={<Planetary />} />
                <Route path="corporation/" element={<Navigate to={`/${ProjectName}/`} replace />} />
                <Route path="corporation/:corporationId/" element={<CorporationLedger />} />
                <Route path="alliance/" element={<Navigate to={`/${ProjectName}/`} replace />} />
                <Route path="alliance/:allianceId/" element={<AllianceLedger />} />
                <Route path="settings/" element={<SettingsPage />} />
                <Route path="superuser/" element={<SuperuserPage />} />
                <Route path="admin/" element={<Navigate to={`/${ProjectName}/superuser/`} replace />} />
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

export default Routing
