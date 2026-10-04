// React
import React from 'react'
import ReactDOM from "react-dom/client";

// Styles
import '@/index.css';
import '@/ledger.css';

import App from '@/App.tsx';

const container = document.getElementById('aa-ledger-root')

if (!container) {
  throw new Error('AA Ledger React mount point was not found.')
}

ReactDOM.createRoot(container).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
