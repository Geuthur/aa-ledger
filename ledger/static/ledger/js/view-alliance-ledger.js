/* global aaLedgerSettings, aaLedgerSettingsOverride, _bootstrapTooltip, _bootstrapPopOver, fetchGet, fetchPost, bootstrap, DataTable, moment, numberFormatter, load_or_create_Chart */

$(document).ready(() => {
    /**
     * Table :: IDs
     */
    const allianceTable = $('#alliance-ledger-table');
    const allianceSummaryTable = $('#alliance-ledger-summary-table');
    const allianceDailyTable = $('#alliance-ledger-daily-table');
    const allianceHourlyTable = $('#alliance-ledger-hourly-table');

    /**
     * Helper: format currency with classes
     */
    const _formatCurrencySpan = (value, positiveClass = 'text-success') => {
        const cls = value > 0 ? positiveClass : (value < 0 ? 'text-danger' : '');
        console.log(aaLedgerSettings.locale);
        const formatted = numberFormatter({
            value: value,
            language: aaLedgerSettings.locale,
            options: {
                style: 'currency',
                currency: 'ISK',
                maximumFractionDigits: 0
            }
        });
        return `<span class="${cls}">${formatted}</span>`;
    };

    /**
     * Modals :: IDs
     */
    const modalRequestViewCorporationLedgerDetails = $('#ledger-view-alliance-ledger-details');

    /**
     * Chart :: IDs
     */
    const chartChord = 'chord-chart';
    const chartXY = 'xy-chart';

    fetchGet({
        url: aaLedgerSettings.url.AllianceLedger,
    })
        .then((data) => {
            if (data) {
                /**
                * DataTable for Corporation Ledger
                * @type {*|jQuery}
                */
                const allianceDataTable = new DataTable(allianceTable, {
                    data: data.corporations,
                    language: aaLedgerSettings.dataTables.language,
                    layout: aaLedgerSettings.dataTables.layout,
                    ordering: aaLedgerSettings.dataTables.ordering,
                    columnControl: aaLedgerSettings.dataTables.columnControl,
                    order: [[5, 'desc']],
                    columnDefs: [
                        {
                            orderable: false,
                            targets: 6,
                            columnControl: [
                                {target: 0, content: []},
                                {target: 1, content: []}
                            ]
                        },
                        {
                            targets: [1,2,3,4,5],
                            type: 'num'
                        },
                        {
                            className: 'border-start',
                            targets: 5
                        }
                    ],
                    columns: [
                        {
                            data: {
                                display: (data) => data.corporation.icon + ' ' + data.corporation.entity_name + ' ' + data.corporation.popover,
                                sort: (data) => data.corporation.entity_name,
                                filter: (data) => data.corporation.entity_name
                            }
                        },
                        {
                            data: {
                                display: (data) => _formatCurrencySpan(data.ledger.bounty),
                                sort: (data) => data.ledger.bounty,
                                filter: (data) => data.ledger.bounty
                            }
                        },
                        {
                            data: {
                                display: (data) => _formatCurrencySpan(data.ledger.ess),
                                sort: (data) => data.ledger.ess,
                                filter: (data) => data.ledger.ess
                            }
                        },
                        {
                            data: {
                                display: (data) => _formatCurrencySpan(data.ledger.miscellaneous),
                                sort: (data) => data.ledger.miscellaneous,
                                filter: (data) => data.ledger.miscellaneous
                            }
                        },
                        {
                            data: {
                                display: (data) => _formatCurrencySpan(data.ledger.costs),
                                sort: (data) => data.ledger.costs,
                                filter: (data) => data.ledger.costs
                            }
                        },
                        {
                            data: {
                                display: (data) => _formatCurrencySpan(data.ledger.total),
                                sort: (data) => data.ledger.total,
                                filter: (data) => data.ledger.total
                            }
                        },
                        {
                            data: 'actions'
                        }
                    ],
                    initComplete: function() {
                        _bootstrapTooltip({selector: '#alliance-ledger-table'});
                        _bootstrapPopOver({selector: '#alliance-ledger-table'});
                    },
                    drawCallback: function () {
                        _bootstrapTooltip({selector: '#alliance-ledger-table'});
                        _bootstrapPopOver({selector: '#alliance-ledger-table'});
                    },
                });

                // Insert totals footer for alliance table
                allianceTable.find('tfoot').html(data.information.footer_html);

                /**
                 * Charts for Corporation Ledger
                 */
                load_or_create_Chart(chartXY, data.billboard.xy_chart, 'bar');
                load_or_create_Chart(chartChord, data.billboard.chord_chart, 'chart');
            }
        })
        .catch((error) => {
            console.error('Error fetching Corporation Ledger data:', error);
        });

    /**
     * Modal :: View Ledger Details :: Table :: Summary Table DataTable
     * Initialize DataTable for View Ledger Details Modal :: Summary Table
     * @type {*|jQuery}
     */
    const summaryDataTable = new DataTable(allianceSummaryTable, {
        data: null, // Loaded via API on modal open
        language: aaLedgerSettings.dataTables.language,
        layout: aaLedgerSettings.dataTables.layout,
        ordering: aaLedgerSettings.dataTables.ordering,
        columnControl: aaLedgerSettings.dataTables.columnControl,
        order: [[0, 'asc']],

        columnDefs: [
            {
                orderable: false,
                targets: [2],
                columnControl: [
                    {target: 0, content: []},
                    {target: 1, content: []}
                ]
            },
            {
                targets: [1],
                type: 'num'
            },
        ],
        columns: [
            {
                data: {
                    display: (data) => data.name,
                    sort: (data) => data.name,
                    filter: (data) => data.name
                }
            },
            {
                data: {
                    display: (data) => _formatCurrencySpan(data.amount),
                    sort: (data) => data.amount,
                    filter: (data) => data.amount
                }
            },
            {
                data:
                {
                    display: (data) => data.ref_types,
                }
            },
        ],
        initComplete: function () {
            _bootstrapTooltip({selector: '#alliance-ledger-summary-table'});
            _bootstrapPopOver({selector: '#alliance-ledger-summary-table'});
        },
        drawCallback: function () {
            _bootstrapTooltip({selector: '#alliance-ledger-summary-table'});
            _bootstrapPopOver({selector: '#alliance-ledger-summary-table'});
        },
    });

    /**
     * Modal :: View Ledger Details :: Table :: Summary Table DataTable
     * Initialize DataTable for View Ledger Details Modal :: Summary Table
     * @type {*|jQuery}
     */
    const dailyDataTable = new DataTable(allianceDailyTable, {
        data: null, // Loaded via API on modal open
        language: aaLedgerSettings.dataTables.language,
        layout: aaLedgerSettings.dataTables.layout,
        ordering: aaLedgerSettings.dataTables.ordering,
        columnControl: aaLedgerSettings.dataTables.columnControl,
        order: [[0, 'asc']],
        columnDefs: [
            {
                orderable: false,
                targets: [2],
                columnControl: [
                    {target: 0, content: []},
                    {target: 1, content: []}
                ]
            },
            {
                targets: [1],
                type: 'num'
            }
        ],
        columns: [
            {
                data: {
                    display: (data) => data.name,
                    sort: (data) => data.name,
                    filter: (data) => data.name
                }
            },
            {
                data: {
                    display: (data) => _formatCurrencySpan(data.amount),
                    sort: (data) => data.amount,
                    filter: (data) => data.amount
                }
            },
            {
                data:
                {
                    display: (data) => data.ref_types,
                }
            },
        ],
        initComplete: function () {
            _bootstrapTooltip({selector: '#alliance-ledger-daily-table'});
            _bootstrapPopOver({selector: '#alliance-ledger-daily-table'});
        },
        drawCallback: function () {
            _bootstrapTooltip({selector: '#alliance-ledger-daily-table'});
            _bootstrapPopOver({selector: '#alliance-ledger-daily-table'});
        },
    });

    /**
     * Modal :: View Ledger Details :: Table :: Summary Table DataTable
     * Initialize DataTable for View Ledger Details Modal :: Summary Table
     * @type {*|jQuery}
     */
    const hourlyDataTable = new DataTable(allianceHourlyTable, {
        data: null, // Loaded via API on modal open
        language: aaLedgerSettings.dataTables.language,
        layout: aaLedgerSettings.dataTables.layout,
        ordering: aaLedgerSettings.dataTables.ordering,
        columnControl: aaLedgerSettings.dataTables.columnControl,
        order: [[0, 'asc']],
        columnDefs: [
            {
                orderable: false,
                targets: [2],
                columnControl: [
                    {target: 0, content: []},
                    {target: 1, content: []}
                ]
            },
            {
                targets: [1],
                type: 'num'
            }
        ],
        columns: [
            {
                data: {
                    display: (data) => data.name,
                    sort: (data) => data.name,
                    filter: (data) => data.name
                }
            },
            {
                data: {
                    display: (data) => _formatCurrencySpan(data.amount),
                    sort: (data) => data.amount,
                    filter: (data) => data.amount
                }
            },
            {
                data:
                {
                    display: (data) => data.ref_types,
                }
            },
        ],
        initComplete: function () {
            _bootstrapTooltip({selector: '#alliance-ledger-hourly-table'});
            _bootstrapPopOver({selector: '#alliance-ledger-hourly-table'});
        },
        drawCallback: function () {
            _bootstrapTooltip({selector: '#alliance-ledger-hourly-table'});
            _bootstrapPopOver({selector: '#alliance-ledger-hourly-table'});
        },
    });

    /**
     * Load Corporation Ledger Details Data into DataTables in the 'ledger-view-alliance-ledger-details' Modal
     * @param {Object} tableData :: Data Object containing Summary, Daily, and Hourly Data Arrays
     */

    const _loadCorporationDetails = (tableData) => {
        const dtSummary = allianceSummaryTable.DataTable();
        dtSummary.clear().rows.add(tableData.summary).draw();
        allianceSummaryTable.find('tfoot').html(tableData.total.summary);

        const dtDaily = allianceDailyTable.DataTable();
        dtDaily.clear().rows.add(tableData.daily).draw();
        allianceDailyTable.find('tfoot').html(tableData.total.daily);

        const dtHourly = allianceHourlyTable.DataTable();
        dtHourly.clear().rows.add(tableData.hourly).draw();
        allianceHourlyTable.find('tfoot').html(tableData.total.hourly);
    };

    /**
     * Clear related DataTables on Close for the 'ledger-view-alliance-ledger-details' Modal
     */
    const _clearCorporationDetails = () => {
        const dtSummary = allianceSummaryTable.DataTable();
        dtSummary.clear().draw();
        allianceSummaryTable.find('tfoot').html('');

        const dtDaily = allianceDailyTable.DataTable();
        dtDaily.clear().draw();
        allianceDailyTable.find('tfoot').html('');

        const dtHourly = allianceHourlyTable.DataTable();
        dtHourly.clear().draw();
        allianceHourlyTable.find('tfoot').html('');
    };

    /**
     * Modal :: Corporation Ledger :: Table :: Info Button Click Handler
     * @const {_loadCorporationDetails} :: Load Corporation Ledger Details Data into DataTables in the 'ledger-view-alliance-ledger-details' Modal
     * @const {_clearCorporationDetails} :: Clear related DataTables on Close
     * When opening, fetch data from the API Endpoint defined in the button's data-action attribute
     * and load it into the Corporation Ledger Details DataTables related to the 'ledger-view-alliance-ledger-details' Modal
     */
    modalRequestViewCorporationLedgerDetails.on('show.bs.modal', (event) => {
        const button = $(event.relatedTarget);
        const url = button.data('action');

        fetchGet({
            url: url,
        })
            .then((data) => {
                if (data) {
                    _loadCorporationDetails(data);
                }
            })
            .catch((error) => {
                console.error('Error fetching Payments Details Modal:', error);
            });
    })
        .on('hide.bs.modal', () => {
            _clearCorporationDetails();
        });
});
