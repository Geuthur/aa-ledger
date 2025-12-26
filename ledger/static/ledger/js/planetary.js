/* global aaLedgerSettings, aaLedgerSettingsOverride, _bootstrapTooltip, fetchGet, fetchPost, bootstrap, DataTable, moment */

$(document).ready(() => {
    /**
     * Table :: IDs
     */
    const planetaryTable = $('#planets-details');
    const storageTable = $('#storage-table');
    const factoryTable = $('#factory-table');
    const extractorTable = $('#extractors-table');
    /**
     * Modals :: IDs
     */
    const modalRequestViewFactory = $('#ledger-view-planetary-factory');
    const modalRequestViewExtractor = $('#ledger-view-planetary-extractor');
    const modalRequestToggleNotification = $('#ledger-accept-planet-toggle-notification');

    /**
     * Translation
     */
    const confirmSwitchAlarm = aaLedgerSettings.translations.confirmSwitchAlarm;
    const switchAlarm = aaLedgerSettings.translations.buttonSwitchAlarm;

    fetchGet({
        url: aaLedgerSettings.url.Planetary,
    })
        .then((data) => {
            if (data) {
            /**
             * Table :: Planetary
             * Initialize DataTable for Planetary Table
             * @type {*|jQuery}
             */
                const planetaryDataTable = new DataTable(planetaryTable, {
                    data: data,
                    language: aaLedgerSettings.dataTables.language,
                    layout: aaLedgerSettings.dataTables.layout,
                    ordering: aaLedgerSettings.dataTables.ordering,
                    columnControl: aaLedgerSettings.dataTables.columnControl,
                    order: [[4, 'desc']],
                    columnDefs: [
                        {
                            orderable: false,
                            targets: [3, 5, 6, 8],
                            columnControl: [
                                {target: 0, content: []},
                                {target: 1, content: []}
                            ]
                        },
                        {
                            targets: [3, 5],
                            width: '20%'
                        },
                        {
                            targets: [2, 8],
                            width: '32px'
                        }
                    ],
                    pageLength: 25,
                    columns: [
                        {
                            data: {
                                display: (data) => data.owner.icon + ' ' + data.owner.character_name,
                                sort: (data) => data.owner.character_name,
                                filter: (data) => data.owner.character_name
                            }
                        },
                        {
                            data: {
                                display: (data) => data.planet.type.icon + ' ' + data.planet.name + data.alarm,
                                sort: (data) => data.planet.name,
                                filter: (data) => data.planet.name
                            }
                        },
                        {
                            data: {
                                display: (data) => data.planet.upgrade_level,
                                sort: (data) => data.planet.upgrade_level,
                                filter: (data) => data.planet.upgrade_level
                            }
                        },
                        {
                            data: {
                                display: (data) => {
                                    const items = data.factories.flatMap(f => f.resource_items);
                                    const icons = Array.from(new Set(items.map(product => product.icon))).join(' ');
                                    return `${icons} ${data.actions.factory_info_button}`;
                                },
                            }
                        },
                        {
                            data: 'progress_bar'
                        },
                        {
                            data: {
                                display: (data) => {
                                    const products = data.factories.map(f => f.product).filter(Boolean);
                                    const icons = Array.from(new Set(products.map(p => p.icon))).join(' ');
                                    return `${icons} ${data.actions.extractor_info_button}`;
                                },
                                sort: (data) => Array.from(new Set(data.factories.map(f => f.product && f.product.item_name))),
                                filter: (data) => Array.from(new Set(data.factories.map(f => f.product && f.product.item_name)))
                            }
                        },
                        {
                            data: {
                                display: (data) => data.expired,
                                sort: (data) => data.expired,
                                filter: (data) => data.expired
                            }
                        },
                        {
                            data: {
                                display: (data) => {
                                    const date = moment(data.planet.last_update);
                                    if (!data.planet.last_update || !date.isValid()) {
                                        return 'N/A';
                                    }
                                    return date.fromNow();
                                },
                                sort: (data) => data.planet.last_update,
                                filter: (data) => data.planet.last_update
                            }
                        },
                        {
                            data: {
                                display: (data) => data.actions.toggle_notification_button,
                            }
                        }
                    ],
                    initComplete: function() {
                        _bootstrapTooltip({selector: '#planets-details' });
                    },
                    drawCallback: function () {
                        _bootstrapTooltip({selector: '#planets-details' });
                    },
                });
            }
        })
        .catch((error) => {
            console.error('Error fetching planetary data:', error);
        });

    /**
     * Modal:: View Factory Details :: Table :: Storage :: Helper Function :: Load Modal DataTable
     * Load data into Storage DataTable and redraw in View Factory Details Modal
     * @param {Object} tableData Ajax API Response Data
     * @private
     */
    const _loadstorageModalDataTable = (tableData) => {
        const dtStorage = storageTable.DataTable();
        dtStorage.clear().rows.add(tableData).draw();
    };

    /**
     * Modal:: View Factory Details :: Table :: Storage :: Helper Function :: Clear Modal DataTable
     * Clear data from Storage DataTable and redraw in View Factory Details Modal
     * @private
     */
    const _clearstorageModalDataTable = () => {
        const dtStorage = storageTable.DataTable();
        dtStorage.clear().draw();
    };

    /**
     * Modal :: View Factory Details :: Table :: Storage Table DataTable
     * Initialize DataTable for View Factory Details Modal :: Storage Table
     * @type {*|jQuery}
     */
    const storageDataTable = new DataTable(storageTable, {
        data: null, // Loaded via API on modal open
        language: aaLedgerSettings.dataTables.language,
        layout: aaLedgerSettings.dataTables.layout,
        ordering: aaLedgerSettings.dataTables.ordering,
        columnControl: aaLedgerSettings.dataTables.columnControl,
        order: [[1, 'desc']],
        columns: [
            {
                data: {
                    display: (data) => data.factory_name,
                    sort: (data) => data.factory_name,
                    filter: (data) => data.factory_name
                }
            },
            {
                data: {
                    display: (data) => data.product.icon + ' ' + data.product.item_name,
                    sort: (data) => data.product.item_name,
                    filter: (data) => data.product.item_name,
                }
            },
            {
                data:
                {
                    display: (data) => data.product.item_quantity.toLocaleString(aaLedgerSettings.locale),
                    sort: (data) => data.product.item_quantity,
                    filter: (data) => data.product.item_quantity,
                }
            },
        ],
        initComplete: function () {
            _bootstrapTooltip({selector: '#storage-table'});
        },
        drawCallback: function () {
            _bootstrapTooltip({selector: '#storage-table'});
        },
    });

    /**
     * Modal:: View Factory Details :: Table :: Factory :: Helper Function :: Load Modal DataTable
     * Load data into Factory DataTable and redraw in View Factory Details Modal
     * @param {Object} tableData Ajax API Response Data
     * @private
     */
    const _loadfactoryModalDataTable = (tableData) => {
        const dtFactory = factoryTable.DataTable();
        dtFactory.clear().rows.add(tableData.factories).draw();

        const dtStorage = storageTable.DataTable();
        dtStorage.clear().rows.add(tableData.storage).draw();
    };

    /**
     * Modal:: View Factory Details :: Table :: Factory :: Helper Function :: Clear Modal DataTable
     * Clear data from Factory DataTable and redraw in View Factory Details Modal
     * @private
     */
    const _clearfactoryModalDataTable = () => {
        const dtFactory = factoryTable.DataTable();
        dtFactory.clear().draw();

        const dtStorage = storageTable.DataTable();
        dtStorage.clear().draw();
    };

    /**
     * Modal :: View Factory Details :: Table :: Factory Table DataTable
     * Initialize DataTable for View Factory Details Modal :: Factory Table
     * @type {*|jQuery}
     */
    const factoryDataTable = new DataTable(factoryTable, {
        data: null, // Loaded via API on modal open
        language: aaLedgerSettings.dataTables.language,
        layout: aaLedgerSettings.dataTables.layout,
        ordering: aaLedgerSettings.dataTables.ordering,
        columnControl: aaLedgerSettings.dataTables.columnControl,
        order: [[0, 'desc']],
        columnDefs: [
            {
                orderable: false,
                targets: [1, 3],
                columnControl: [
                    {target: 0, content: []},
                    {target: 1, content: []}
                ]
            }
        ],
        columns: [
            {
                data: {
                    display: (data) => data.factory_name,
                    sort: (data) => data.factory_name,
                    filter: (data) => data.factory_name
                }
            },
            {
                data: {
                    display: (data) => Object.values(data.resource_items).map(ressource => ressource.icon),
                    sort: (data) => Object.values(data.resource_items).map(ressource => ressource.item_name),
                    filter: (data) => Object.values(data.resource_items).map(ressource => ressource.item_name)
                }
            },
            {
                data:
                {
                    display: (data) => data.product.icon + ' ' + data.product.item_name,
                    sort: (data) => data.product.item_name,
                    filter: (data) => data.product.item_name
                }
            },
            {
                data:
                {
                    display: (data) => data.is_active,
                    sort: (data) => data.is_active,
                    filter: (data) => data.is_active
                }
            },
        ],
        initComplete: function () {
            _bootstrapTooltip({selector: '#factory-table'});
        },
        drawCallback: function () {
            _bootstrapTooltip({selector: '#factory-table'});
        },
    });

    /**
     * Modal :: Factory :: Info Button Click Handler
     * @const {_loadfactoryModalDataTable} :: Load Factory Data into Factory DataTable in the Factory Modal
     * @const {_clearfactoryModalDataTable} :: Clear related DataTable on Close
     * When opening, fetch data from the API Endpoint defined in the button's data-action attribute
     * and load it into the Factory DataTable related to the Factory Modal
     */
    modalRequestViewFactory.on('show.bs.modal', (event) => {
        const button = $(event.relatedTarget);
        const url = button.data('action');

        // guard clause for previous Modal reload function
        if (!url) {
            return;
        }

        fetchGet({
            url: url,
        })
            .then((data) => {
                if (data) {
                    _loadfactoryModalDataTable(data);
                }
            })
            .catch((error) => {
                console.error('Error fetching Factory Modal:', error);
            });
    })
        .on('hide.bs.modal', () => {
            _clearfactoryModalDataTable();
        });

    /**
     * Modal :: View Extractor Details :: Table :: Extractors Table DataTable
     * Initialize DataTable for View Extractor Details Modal :: Extractors Table
     * @type {*|jQuery}
     */
    const extractorDataTable = new DataTable(extractorTable, {
        data: null, // Loaded via API on modal open
        language: aaLedgerSettings.dataTables.language,
        layout: aaLedgerSettings.dataTables.layout,
        ordering: aaLedgerSettings.dataTables.ordering,
        columnControl: aaLedgerSettings.dataTables.columnControl,
        order: [[0, 'desc']],
        columns: [
            {
                data: {
                    display: (data) => data.icon + ' ' + data.item_name,
                    sort: (data) => data.item_name,
                    filter: (data) => data.item_name
                }
            },
            {
                data: {
                    display: (data) => {
                        const date = moment(data.install_time);
                        if (!data.install_time || !date.isValid()) {
                            return 'N/A';
                        }
                        return date.fromNow();
                    },
                    sort: (data) => data.install_time,
                    filter: (data) => data.install_time
                }
            },
            {
                data:
                {
                    display: (data) => {
                        const date = moment(data.expiry_time);
                        if (!data.expiry_time || !date.isValid()) {
                            return 'N/A';
                        }
                        return date.fromNow();
                    },
                    sort: (data) => data.expiry_time,
                    filter: (data) => data.expiry_time
                }
            },
            {
                data:
                {
                    display: (data) => data.progress.html,
                    sort: (data) => data.progress.percentage,
                    filter: (data) => data.progress.percentage
                }
            },
        ],
        initComplete: function () {
            _bootstrapTooltip({selector: '#extractors-table'});
        },
        drawCallback: function () {
            _bootstrapTooltip({selector: '#extractors-table'});
        },
    });

    /**
     * Modal:: View Extractor Details :: Table :: Extractor :: Helper Function :: Load Modal DataTable
     * Load data into Extractor DataTable and redraw in View Extractor Details Modal
     * @param {Object} tableData Ajax API Response Data
     * @private
     */
    const _loadextractorModalDataTable = (tableData) => {
        const dtExtractor = extractorTable.DataTable();
        dtExtractor.clear().rows.add(tableData.extractors).draw();
    };

    /**
     * Modal:: View Extractor Details :: Table :: Extractor :: Helper Function :: Clear Modal DataTable
     * Clear data from Extractor DataTable and redraw in View Extractor Details Modal
     * @private
     */
    const _clearextractorModalDataTable = () => {
        const dtExtractor = extractorTable.DataTable();
        dtExtractor.clear().draw();
    };

    /**
     * Modal :: Extractor :: Info Button Click Handler
     * @const {_loadextractorModalDataTable} :: Load Extractor Data into Extractor DataTable in the Extractor Modal
     * @const {_clearextractorModalDataTable} :: Clear related DataTable on Close
     * When opening, fetch data from the API Endpoint defined in the button's data-action attribute
     * and load it into the Extractor DataTable related to the Extractor Modal
     */
    modalRequestViewExtractor.on('show.bs.modal', (event) => {
        const button = $(event.relatedTarget);
        const url = button.data('action');

        // guard clause for previous Modal reload function
        if (!url) {
            return;
        }

        fetchGet({
            url: url,
        })
            .then((data) => {
                if (data) {
                    _loadextractorModalDataTable(data);
                }
            })
            .catch((error) => {
                console.error('Error fetching Extractor Modal:', error);
            });
    })
        .on('hide.bs.modal', () => {
            _clearextractorModalDataTable();
        });

    /**
     * Table :: Planetary :: Reload DataTable
     * Reload the Planetary DataTable with new data
     * @param {Array} newData - New data to load into the DataTable
     * @returns {void}
     */
    function _reloadPlanetaryDataTable(newData) {
        const dtPlanetary = planetaryTable.DataTable();
        dtPlanetary.clear().rows.add(newData).draw();
    }

    /**
     * Table :: Planetary :: Toggle Notification Button Click Handler
     * Open Confirm Toggle Notification Modal
     * On Confirmation send a request to the API Endpoint and close the modal
     */
    modalRequestToggleNotification.on('show.bs.modal', (event) => {
        const button = $(event.relatedTarget);
        const url = button.data('action');
        const form = modalRequestToggleNotification.find('form');
        const csrfMiddlewareToken = form.find('input[name="csrfmiddlewaretoken"]').val();

        modalRequestToggleNotification.find('#modal-button-confirm-accept-request').on('click', () => {
            fetchPost({
                url: url,
                csrfToken: csrfMiddlewareToken,
            })
                .then((data) => {
                    if (data.success === true) {
                        fetchGet({
                            url: aaLedgerSettings.url.Planetary,
                        })
                            .then((newData) => {
                                if (newData) {
                                    _reloadPlanetaryDataTable(newData);
                                }
                            })
                            .catch((error) => {
                                console.error('Error fetching planetary data:', error);
                            });
                        modalRequestToggleNotification.modal('hide');
                    }
                })
                .catch((error) => {
                    console.error(`Error posting switch notification request: ${error.message}`);
                });
        });
    })
        .on('hide.bs.modal', () => {
            modalRequestToggleNotification.find('#modal-button-confirm-accept-request').unbind('click');
        });
});
