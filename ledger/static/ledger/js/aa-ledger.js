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
