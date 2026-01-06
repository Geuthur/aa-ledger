/* global aaLedgerDefaultSettings, aaLedgerSettingsOverride, objectDeepMerge, bootstrap */

/**
 * Default settings for aa-ledger
 * Settings can be overridden by defining aaLedgerSettingsOverride before this script is loaded.
 */
const aaLedgerSettings = (typeof aaLedgerSettingsOverride !== 'undefined')
    ? objectDeepMerge(aaLedgerDefaultSettings, aaLedgerSettingsOverride) // jshint ignore:line
    : aaLedgerDefaultSettings;

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
 * Export HTML table to CSV file (DataTables-only)
 *
 * This function exports the contents of a DataTables-enhanced HTML table to a CSV file.
 *
 * @param {HTMLElement} table HTML table element enhanced by DataTables
 * @param {number} columnIndex Index of the column to exclude from export (e.g., actions column)
 * @param {string} filename Name of the CSV file to be downloaded
 * @returns {void}
 */
const _exportTableToCSV = (dt, columnIndex, filename = 'ledger.csv') => {
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
            let raw = '';
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
