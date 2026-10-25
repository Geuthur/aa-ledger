// React
import React from 'react'
import ReactDOM from "react-dom/client";

// Third Party
import i18n from "i18next";
import Backend from "i18next-http-backend";
import { initReactI18next } from "react-i18next";

// Styles
import '@/Styles/index.css';
import '@/Styles/ledger.css';
import '@/Styles/table.css';

import { AppName, ProjectName } from '@/constants';
import Routing from '@/Routing';
export { AppName, ProjectName };

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

const container = typeof document !== "undefined" ? document.getElementById('aa-ledger-root') : null;

if (container) {
  ReactDOM.createRoot(container).render(
    <React.StrictMode>
      <Routing />
    </React.StrictMode>,
  );
}

