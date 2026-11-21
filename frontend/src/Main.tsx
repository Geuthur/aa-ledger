/* eslint-disable import-headings/import-headings -- the global index.css must load before the CSS modules */
// React
import React from 'react'
import ReactDOM from "react-dom/client";

// Third Party
import { initI18n } from "aa-geuthur-react";

// Styles
import '@/Styles/index.css';
import '@/Styles/ledger.css';

import { AppName, ProjectName } from '@/constants';
import Routing from '@/Routing';
export { AppName, ProjectName };

// Language from the lang attribute of the root element, texts from /static/<project>/i18n/<lng>/translation.json
initI18n(ProjectName, `${AppName}-root`);

const container = typeof document !== "undefined" ? document.getElementById(`${AppName}-root`) : null;

if (container) {
  ReactDOM.createRoot(container).render(
    <React.StrictMode>
      <Routing />
    </React.StrictMode>,
  );
}

