/* global aaLedgerSettings, aaLedgerSettingsOverride, _bootstrapTooltip, _bootstrapPopOver, fetchGet, fetchPost, bootstrap, DataTable, moment, numberFormatter, load_or_create_Chart */

$(document).ready(() => {
    /**
     * Table :: IDs
     */
    const characterTable = $('#character-ledger-table');
    const characterSummaryTable = $('#character-ledger-summary-table');
    const characterDailyTable = $('#character-ledger-daily-table');
    const characterHourlyTable = $('#character-ledger-hourly-table');

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
    const modalRequestViewCharacterLedgerDetails = $('#ledger-view-character-ledger-details');

    /**
     * Chart :: IDs
     */
    const chartChord = 'chord-chart';
    const chartXY = 'xy-chart';

    /**
     * DropDowns :: IDs
     */
    const dropdownButtons = $('#character-ledger-dropdown-buttons');

    fetchGet({
        url: aaLedgerSettings.url.CharacterLedger,
    })
        .then((data) => {
            if (data) {
                /**
                * DataTable for Character Ledger
                * @type {*|jQuery}
                */
                const characterDataTable = new DataTable(characterTable, {
                    data: data.characters,
                    language: aaLedgerSettings.dataTables.language,
                    layout: aaLedgerSettings.dataTables.layout,
                    ordering: aaLedgerSettings.dataTables.ordering,
                    columnControl: aaLedgerSettings.dataTables.columnControl,
                    order: [[6, 'desc']],
                    columnDefs: [
                        {
                            orderable: false,
                            targets: 7,
                            columnControl: [
                                {target: 0, content: []},
                                {target: 1, content: []}
                            ]
                        },
                        {
                            targets: [1,2,3,4,5,6],
                            type: 'num'
                        },
                        {
                            className: 'border-start',
                            targets: 6
                        }
                    ],
                    columns: [
                        {
                            data: {
                                display: (data) => data.character.icon + ' ' + data.character.character_name,
                                sort: (data) => data.character.character_name,
                                filter: (data) => data.character.character_name
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
                                display: (data) => _formatCurrencySpan(data.ledger.mining, 'text-info'),
                                sort: (data) => data.ledger.mining,
                                filter: (data) => data.ledger.mining
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
                        _bootstrapTooltip({selector: '#character-ledger-table'});
                    },
                    drawCallback: function () {
                        _bootstrapTooltip({selector: '#character-ledger-table'});
                    },
                });

                // Insert totals footer for character table
                characterTable.find('tfoot').html(data.information.footer_html);

                /**
                 * Charts for Character Ledger
                 */
                load_or_create_Chart(chartXY, data.billboard.xy_chart, 'bar');
                load_or_create_Chart(chartChord, data.billboard.chord_chart, 'chart');
                // Insert Dropdown Buttons HTML
                dropdownButtons.html(data.information.dropdown_html);
            }
        })
        .catch((error) => {
            console.error('Error fetching Character Ledger data:', error);
        });

    /**
     * Modal :: View Ledger Details :: Table :: Summary Table DataTable
     * Initialize DataTable for View Ledger Details Modal :: Summary Table
     * @type {*|jQuery}
     */
    const summaryDataTable = new DataTable(characterSummaryTable, {
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
            _bootstrapTooltip({selector: '#character-ledger-summary-table'});
            _bootstrapPopOver({selector: '#character-ledger-summary-table'});
        },
        drawCallback: function () {
            _bootstrapTooltip({selector: '#character-ledger-summary-table'});
            _bootstrapPopOver({selector: '#character-ledger-summary-table'});
        },
    });

    /**
     * Modal :: View Ledger Details :: Table :: Summary Table DataTable
     * Initialize DataTable for View Ledger Details Modal :: Summary Table
     * @type {*|jQuery}
     */
    const dailyDataTable = new DataTable(characterDailyTable, {
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
            _bootstrapTooltip({selector: '#character-ledger-daily-table'});
            _bootstrapPopOver({selector: '#character-ledger-daily-table'});
        },
        drawCallback: function () {
            _bootstrapTooltip({selector: '#character-ledger-daily-table'});
            _bootstrapPopOver({selector: '#character-ledger-daily-table'});
        },
    });

    /**
     * Modal :: View Ledger Details :: Table :: Summary Table DataTable
     * Initialize DataTable for View Ledger Details Modal :: Summary Table
     * @type {*|jQuery}
     */
    const hourlyDataTable = new DataTable(characterHourlyTable, {
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
            _bootstrapTooltip({selector: '#character-ledger-hourly-table'});
            _bootstrapPopOver({selector: '#character-ledger-hourly-table'});
        },
        drawCallback: function () {
            _bootstrapTooltip({selector: '#character-ledger-hourly-table'});
            _bootstrapPopOver({selector: '#character-ledger-hourly-table'});
        },
    });

    /**
     * Load Character Ledger Details Data into DataTables in the 'ledger-view-character-ledger-details' Modal
     * @param {Object} tableData :: Data Object containing Summary, Daily, and Hourly Data Arrays
     */

    const _loadCharacterDetails = (tableData) => {
        const dtSummary = characterSummaryTable.DataTable();
        dtSummary.clear().rows.add(tableData.summary).draw();
        characterSummaryTable.find('tfoot').html(tableData.total.summary);

        const dtDaily = characterDailyTable.DataTable();
        dtDaily.clear().rows.add(tableData.daily).draw();
        characterDailyTable.find('tfoot').html(tableData.total.daily);

        const dtHourly = characterHourlyTable.DataTable();
        dtHourly.clear().rows.add(tableData.hourly).draw();
        characterHourlyTable.find('tfoot').html(tableData.total.hourly);
    };

    /**
     * Clear related DataTables on Close for the 'ledger-view-character-ledger-details' Modal
     */
    const _clearCharacterDetails = () => {
        const dtSummary = characterSummaryTable.DataTable();
        dtSummary.clear().draw();
        characterSummaryTable.find('tfoot').html('');

        const dtDaily = characterDailyTable.DataTable();
        dtDaily.clear().draw();
        characterDailyTable.find('tfoot').html('');

        const dtHourly = characterHourlyTable.DataTable();
        dtHourly.clear().draw();
        characterHourlyTable.find('tfoot').html('');
    };

    /**
     * Modal :: Character Ledger :: Table :: Info Button Click Handler
     * @const {_loadCharacterDetails} :: Load Character Ledger Details Data into DataTables in the 'ledger-view-character-ledger-details' Modal
     * @const {_clearCharacterDetails} :: Clear related DataTables on Close
     * When opening, fetch data from the API Endpoint defined in the button's data-action attribute
     * and load it into the Character Ledger Details DataTables related to the 'ledger-view-character-ledger-details' Modal
     */
    modalRequestViewCharacterLedgerDetails.on('show.bs.modal', (event) => {
        const button = $(event.relatedTarget);
        const url = button.data('action');

        fetchGet({
            url: url,
        })
            .then((data) => {
                if (data) {
                    _loadCharacterDetails(data);
                }
            })
            .catch((error) => {
                console.error('Error fetching Payments Details Modal:', error);
            });
    })
        .on('hide.bs.modal', () => {
            _clearCharacterDetails();
        });
});
