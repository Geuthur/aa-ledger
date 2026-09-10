/* global aaLedgerDefaultSettings, aaLedgerSettingsOverride, objectDeepMerge, bootstrap */

/**
 * Default settings for aa-ledger
 * Settings can be overridden by defining aaLedgerSettingsOverride before this script is loaded.
 */
const aaLedgerSettings = (typeof aaLedgerSettingsOverride !== 'undefined')
    ? objectDeepMerge(aaLedgerDefaultSettings, aaLedgerSettingsOverride) // jshint ignore:line
    : aaLedgerDefaultSettings;


/**
* Local fetch adapter: keeps global fetch helpers untouched while improving error details.
* Reads JSON error payload (message/error/detail) when statusText is empty.
* @param {string} url The URL to fetch data from.
* @param {string} [method=GET] The HTTP method to use for the request.
* @param {Object|null} [payload=null] The request payload for POST requests.
* @param {string|null} [csrfToken=null] The CSRF token for POST requests.
* @param {boolean} [responseIsJson=true] Whether the response is expected to be JSON.
* @returns {Promise<Object|string>} The response data, either as JSON or text.
* @throws {Error} If the request fails or the response is not OK.
*/
const fetchData = async ({
    url,
    method = 'GET',
    payload = null,
    csrfToken = null,
    responseIsJson = true
}) => {
    let requestUrl = url;

    if (payload !== null && (typeof payload !== 'object' || Array.isArray(payload))) {
        throw new Error(`Payload must be an object when using ${method} method`);
    }

    const headers = {};
    const request = {
        method,
        headers,
    };

    if (method === 'GET' && payload) {
        const queryParams = new URLSearchParams(payload).toString(); // jshint ignore:line
        requestUrl += (url.includes('?') ? '&' : '?') + queryParams;
    }

    if (method === 'POST') {
        if (!csrfToken) {
            throw new Error('CSRF token is required for POST requests');
        }

        headers['X-CSRFToken'] = csrfToken;
        request.body = payload ? JSON.stringify(payload) : null;
    }

    if (responseIsJson) {
        headers.Accept = 'application/json'; // jshint ignore:line
    }

    if (method === 'POST' && responseIsJson) {
        headers['Content-Type'] = 'application/json';
    }

    const response = await fetch(requestUrl, request);

    if (!response.ok) {
        let details;
        const contentType = (response.headers.get('content-type') || '').toLowerCase();

        try {
            if (contentType.includes('application/json')) {
                const data = await response.clone().json();
                details = data?.message || data?.error || data?.detail || '';
            } else {
                details = (await response.clone().text()).trim();
            }
        } catch (parseError) {
            details = '';
        }

        const statusText = (response.statusText || '').trim() || 'HTTP Error';
        const msg = details
            ? `Error: ${response.status} - ${statusText} | ${details}`
            : `Error: ${response.status} - ${statusText}`;

        throw new Error(msg);
    }

    return responseIsJson ? await response.json() : await response.text();
};

/**
 * Bootstrap tooltip by (@ppfeufer)
 *
 * @param {string} [selector=body] Selector for the tooltip elements, defaults to 'body'
 *                                 to apply to all elements with the data-bs-tooltip attribute.
 *                                 Example: 'body', '.my-tooltip-class', '#my-tooltip-id'
 *                                 If you want to apply it to a specific element, use that element's selector.
 *                                 If you want to apply it to all elements with the data-bs-tooltip attribute,
 *                                 use 'body' or leave it empty.
 * @param {string} [namespace=aa-ledger] Namespace for the tooltip
 * @param {string} [trigger=hover] Trigger for the tooltip ('hover', 'click', etc.)
 * @returns {void}
 */
const _bootstrapTooltip = ({selector = 'body', namespace = 'aa-ledger', trigger = 'hover'} = {}) => {
    document.querySelectorAll(`${selector} [data-bs-tooltip="${namespace}"]`)
        .forEach((tooltipTriggerEl) => {
            // Dispose existing tooltip instance if it exists
            const existing = bootstrap.Tooltip.getInstance(tooltipTriggerEl);
            if (existing) {
                existing.dispose();
            }

            // Remove any leftover tooltip elements
            $('.bs-tooltip-auto').remove();

            // Create new tooltip instance
            return new bootstrap.Tooltip(tooltipTriggerEl, { trigger });
        });
};

const _bootstrapPopOver = ({selector = 'body', namespace = 'aa-ledger', trigger = 'hover'} = {}) => {
    document.querySelectorAll(`${selector} [data-bs-popover="${namespace}"]`)
        .forEach((popoverTriggerEl) => {
            // Dispose existing popover instance if it exists
            const existing = bootstrap.Popover.getInstance(popoverTriggerEl);
            if (existing) {
                existing.dispose();
            }

            // Remove any leftover popover elements
            $('.bs-popover-auto').remove();

            // Create new popover instance
            return new bootstrap.Popover(popoverTriggerEl, { trigger });
        });
};

/**
 * Export a DataTables instance to CSV.
 * @param {object} DataTable - The DataTables instance.
 * @param {string} [exportFileName='aa-ledger.csv'] - The name of the exported CSV file.
 * @throws Will throw an error if the table is not a valid DataTables instance.
 * @returns {void}
 */
const _exportToCSV = (DataTable, exportFileName = 'aa-ledger.csv') => {
    if (!DataTable || typeof DataTable.columns !== 'function') {
        throw new Error('exportToCSV expects a DataTables instance');
    }

    const escapeCsv = (value) => {
        const str = value == null ? '' : String(value);
        return /[",\n\r]/.test(str) ? `"${str.replace(/"/g, '""')}"` : str;
    };

    const headerCells = DataTable.columns().header().toArray();
    const colCount = DataTable.columns().count();
    const rowIndexes = DataTable.rows({ search: 'applied', page: 'all' }).indexes().toArray();

    const headerRow = Array.from({ length: colCount }, (_, index) => {
        const cell = headerCells[index];
        return cell ? (cell.innerText || cell.textContent || '').trim() : '';
    });

    const rows = rowIndexes.map((rowIndex) => Array.from({ length: colCount }, (_, index) => {
        try {
            return DataTable.cell(rowIndex, index).render('sort');
        } catch (error) {
            console.log(`Error retrieving cell data for row ${rowIndex}, column ${index}:`, error);
            return '';
        }
    }));

    const csv = [headerRow, ...rows]
        .map((line) => line.map(escapeCsv).join(','))
        .join('\n');

    const link = document.createElement('a');
    link.download = exportFileName;
    link.href = URL.createObjectURL(new Blob([csv], { type: 'text/csv;charset=utf-8;' }));
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(link.href);
};

/**
 * Export HTML table to CSV file (DataTables-only)
 *
 * This function exports the contents of a DataTables-enhanced HTML table to a CSV file.
 *
 * @param {HTMLElement} table HTML table element enhanced by DataTables
 * @param {number} columnIndex Index of the column to exclude from export (e.g., actions column)
 * @param {string} filename Name of the CSV file to be downloaded (default: 'aa-ledger.csv')
 * @returns {void}
 */
const _exportTableToCSV = (dt, columnIndex, filename = 'aa-ledger.csv') => {
    const csv = [];

    let headerCells = [];
    // Get header cells from DataTables API
    try {
        headerCells = dt.columns().header().toArray();
    } catch (e) {
        console.log('Error retrieving DataTables column headers for CSV export:', e);
    }

    // Determine columns to export (exclude specified column)
    const colCount = dt.columns().count();
    let exportColIndexes = [];
    for (let i = 0; i < colCount; i++) exportColIndexes.push(i);
    exportColIndexes = exportColIndexes.filter(i => i !== columnIndex);

    // Header row
    const headerRow = [];
    for (let ci = 0; ci < exportColIndexes.length; ci++) {
        const colIndex = exportColIndexes[ci];
        const cell = headerCells[colIndex];
        const raw = cell ? (cell.innerText || cell.textContent || '') : '';
        headerRow.push(raw);
    }
    csv.push(headerRow.join(','));

    // Process rows by index and download CSV (use sort cell values)
    const rowIndexes = dt.rows({ search: 'applied', page: 'all' }).indexes().toArray();
    for (let ri = 0; ri < rowIndexes.length; ri++) {
        const rowIndex = rowIndexes[ri];
        const row = [];
        for (let k = 0; k < exportColIndexes.length; k++) {
            const ci = exportColIndexes[k];
            let raw;
            try {
                const renderMode = 'sort';
                raw = dt.cell(rowIndex, ci).render(renderMode);
            } catch (e) {
                console.log(`Error retrieving cell data for row ${rowIndex}, column ${ci}:`, e);
                raw = '';
            }
            row.push(raw);
        }
        csv.push(row.join(','));
    }

    // Download CSV file
    const csvFile = new Blob([csv.join('\n')], { type: 'text/csv' });
    const downloadLink = document.createElement('a');
    downloadLink.download = filename;
    downloadLink.href = window.URL.createObjectURL(csvFile);
    downloadLink.style.display = 'none';
    document.body.appendChild(downloadLink);
    downloadLink.click();
    document.body.removeChild(downloadLink);
};
