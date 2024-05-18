var total_amount, total_amount_ess, total_amount_mining, total_amount_others, total_amount_combined;
var yearTableInitialized = false;  // Flag to check if the year DataTable is initialized
var rattingBar_1, rattingBar_2, chart_wallet_1, chart_wallet_2, gauge_1, gauge_2;
var selectedMonth;
var bb, d3;

document.addEventListener('DOMContentLoaded', function () {
    // Aktuelles Datumobjekt erstellen
    var currentDate = new Date();

    // Aktuelles Jahr und Monat abrufen
    var currentYear = currentDate.getFullYear();
    selectedMonth = currentDate.getMonth() + 1; // +1, um 1-basierten Monat zu erhalten

    $('#monthDropdown').change(function() {
        selectedMonth = $(this).val(); // Ausgewählter Monat auslesen
        var selectedYear = currentYear; // Hier die Logik zum Auslesen des ausgewählten Jahres implementieren, falls nötig
        var monthText = getMonthName(selectedMonth);

        // URL für die Daten der ausgewählten Kombination von Jahr und Monat erstellen
        var url = '/ledger/api/account/0/ledger/year/' + selectedYear + '/month/' + selectedMonth + '/';

        // DataTable neu laden mit den Daten des ausgewählten Monats
        MonthTable.ajax.url(url).load();
        $('#currentMonthLink').text('Month - ' + monthText);
    });

    function getMonthName(monthNumber) {
        var months = [
            'January', 'February', 'March', 'April', 'May', 'June',
            'July', 'August', 'September', 'October', 'November', 'December'
        ];

        // Monatsname abrufen (Beachten Sie die Index-Verschiebung, da Monate bei 1 beginnen)
        return months[parseInt(monthNumber) - 1];
    }

    // Dropdown-Menü auf den aktuellen Monat setzen
    document.getElementById('monthDropdown').value = selectedMonth;
    // Dropdown-Menü anzeigen, nachdem der Monat ausgewählt wurde
    document.getElementById('monthDropdown').style.display = 'block';

    // Function to format currency and apply color
    function formatAndColor(value) {
        // Formatieren und Komma-Stellen entfernen
        var formattedValue = new Intl.NumberFormat('de-DE', { minimumFractionDigits: 0, maximumFractionDigits: 0 }).format(value);

        // Bestimme die Textfarbe basierend auf dem Wert
        var color = value >= 0 ? 'chartreuse' : 'red';

        // Rückgabe des formatierten Strings mit Farbe und Einheit
        return '<span style="color: ' + color + ';">' + formattedValue + '</span> ISK';
    }

    // Initialize DataTable for current_month
    var MonthTable = $('#ratting').DataTable({
        ajax: {
            url: '/ledger/api/account/0/ledger/year/' + currentYear + '/month/' + selectedMonth + '/',
            dataSrc: function (data) {
                // Zusätzliche Daten im DataTable-Objekt speichern
                total_amount = data.items[0].total.total_amount;
                total_amount_ess = data.items[0].total.total_amount_ess;
                total_amount_others = data.items[0].total.total_amount_others;
                total_amount_mining = data.items[0].total.total_amount_mining;
                total_amount_combined = data.items[0].total.total_amount_all;

                // Billboard
                // Wallet Chart
                if (data.items[0].billboard.walletcharts) {
                    $('#walletChartContainer').show(); // Container anzeigen, wenn Daten vorhanden sind
                    var maxpg = 0;
                    data.items[0].billboard.walletcharts.forEach(function (arr) {
                        if (maxpg < arr[0]) {
                            maxpg = arr[0];
                        }
                    });
                    if (chart_wallet_1) {
                        chart_wallet_1.load({
                            columns: data.items[0].billboard.walletcharts,
                            resizeAfter: true,
                        });
                    } else {
                        chart_wallet_1 = bb.generate({
                            data: {
                                columns: data.items[0].billboard.walletcharts,
                                type: 'donut'
                            },
                            colors: {
                                'Market Cost': '#ff0000',
                                'Production Cost': '#ff0000',
                                'Other Costs': '#ff0000',
                                'Earns': '#00ff00',
                            },
                            bindto: '#walletChart'
                        });
                    }
                } else {
                    $('#walletChartContainer').hide(); // Container verstecken, wenn keine Daten vorhanden sind
                }

                // Ratting Bar
                if (data.items[0].billboard.rattingbar) {
                    $('#rattingBarContainer').show(); // Container anzeigen, wenn Daten vorhanden sind
                    var pgs = data.items[0].billboard.rattingbar.filter(arr => arr[0] !== 'x').map(arr => arr[0]);
                    if (rattingBar_1) {
                        rattingBar_1.load({
                            columns: data.items[0].billboard.rattingbar,
                            groups: [pgs],
                            resizeAfter: true,
                        });
                    } else {
                        rattingBar_1 = bb.generate({
                            data: {
                                x: 'x',
                                columns: data.items[0].billboard.rattingbar,
                                type: 'bar',
                                groups: [pgs],
                            },
                            axis: {
                                x: {
                                    padding: { right: 8000 * 60 * 60 * 12 },
                                    type: 'timeseries',
                                    tick: { format: '%Y-%m-%d', rotate: 45 }
                                },
                                y: {
                                    tick: { format: d3.format(',') },
                                    label: 'ISK'
                                },
                            },
                            bindto: '#rattingBar',
                        });
                    }
                } else {
                    $('#rattingBarContainer').hide(); // Container verstecken, wenn keine Daten vorhanden sind
                }

                // Workflow Gauge
                if (data.items[0].billboard.workflowgauge) {
                    $('#workGaugeContainer').show(); // Container anzeigen, wenn Daten vorhanden sind
                    if (gauge_1) {
                        gauge_1.load({
                            columns: data.items[0].billboard.workflowgauge
                        });
                    } else {
                        gauge_1 = bb.generate({
                            data: {
                                columns: data.items[0].billboard.workflowgauge,
                                type: 'gauge'
                            },
                            bindto: '#workGauge'
                        });
                    }
                } else {
                    $('#workGaugeContainer').hide(); // Container verstecken, wenn keine Daten vorhanden sind
                }

                return data.items[0].ratting;
            },
            cache: false
        },
        'processing': true,
        columns: [
            {
                data: 'main_name',
                render: function (data, type, row) {
                    var imageHTML = '<img src="https://images.evetech.net/characters/' + row.main_id + '/portrait?size=32" class="rounded-circle" title="' + data + '" height="30">';
                    return imageHTML + ' ' + data;
                }
            },
            {   data: 'total_amount',
                render: function (data, type, row) {
                    // Rückgabe des formatierten Strings mit Farbe und Einheit
                    if (type === 'display') {
                        return formatAndColor(data);
                    }
                    return data;
                }
            },
            {   data: 'total_amount_ess',
                render: function (data, type, row) {
                    // Rückgabe des formatierten Strings mit Farbe und Einheit
                    if (type === 'display') {
                        return formatAndColor(data);
                    }
                    return data;
                }
            },
            {   data: 'total_amount_mining',
                render: function (data, type, row) {
                    // Rückgabe des formatierten Strings mit Farbe und Einheit
                    if (type === 'display') {
                        return formatAndColor(data);
                    }
                    return data;
                }
            },
            {   data: 'total_amount_others',
                render: function (data, type, row) {
                    // Rückgabe des formatierten Strings mit Farbe und Einheit
                    if (type === 'display') {
                        return formatAndColor(data);
                    }
                    return data;
                }
            },
            // Add more columns as needed
            {
                data: 'col-total-action',
                render: function (data, type, row) {
                    return '<button class="btn btn-sm btn-info btn-square" ' +
                            'data-bs-toggle="modal" ' +
                            'data-bs-target="#modalViewCharacterContainer" ' +
                            'aria-label="' + row.main_name + '" ' +
                            'data-ajax_url="/ledger/api/account/'+ row.main_id + '/ledger/template/year/' + currentYear + '/month/' + selectedMonth + '/" ' +
                            'title="' + row.main_name + '">' +
                            '<span class="fas fa-info"></span>' +
                            '</button>';
                }
            },
        ],
        order: [[2, 'desc']],
        autoWidth: false,
        columnDefs: [
            { sortable: false, targets: [5] },
        ],
        footerCallback: function () {
            var totalAmountAllChars = parseFloat(total_amount);
            var totalEssAmountAllChars = parseFloat(total_amount_ess);
            var totalMiningAmountAllChars = parseFloat(total_amount_mining);
            var totalOthersAmountAllChars = parseFloat(total_amount_others);
            var totalCombinedAmountAllChars = parseFloat(total_amount_combined);
            $('#foot .col-total-amount').html('' + formatAndColor(totalAmountAllChars) + '');
            $('#foot .col-total-ess').html('' + formatAndColor(totalEssAmountAllChars) + '');
            $('#foot .col-total-mining').html('' + formatAndColor(totalMiningAmountAllChars) + '');
            $('#foot .col-total-others').html('' + formatAndColor(totalOthersAmountAllChars) + '');
            $('#foot .col-total-gesamt').html('' + formatAndColor(totalCombinedAmountAllChars) + '');
            $('#foot .col-total-button').html('<button class="btn btn-sm btn-info btn-square" data-bs-toggle="modal" data-bs-target="#modalViewCharacterContainer"' +
                'aria-label="{{ data.main_name }}"' +
                'data-ajax_url="/ledger/api/account/0/ledger/template/year/' + currentYear + '/month/' + selectedMonth + '/" ' +
                'title="{{ data.main_name }}"> <span class="fas fa-info"></span></button>');
        },
    });

    $('a[data-bs-toggle="tab"]').on('shown.bs.tab', function (e) {
        // Get the id of the tab that was clicked
        var targetTabId = $(e.target).attr('href');

        // Check if the clicked tab is the one containing the year DataTable
        if (targetTabId === '#tab-all_month' && !yearTableInitialized) {
            // Initialisiere DataTable für den Hauptinhalt
            var YearTable = $('#ratting_year').DataTable({
                ajax: {
                    url: '/ledger/api/account/0/ledger/year/' + currentYear + '/month/0/',
                    dataSrc: function (data) {
                        // Zusätzliche Daten im DataTable-Objekt speichern
                        total_amount = data.items[0].total.total_amount;
                        total_amount_ess = data.items[0].total.total_amount_ess;
                        total_amount_mining = data.items[0].total.total_amount_mining;
                        total_amount_others = data.items[0].total.total_amount_others;
                        total_amount_combined = data.items[0].total.total_amount_all;

                        // Billboard
                        // Wallet Chart
                        if (data.items[0].billboard.walletcharts) {
                            var maxpg = 0;
                            data.items[0].billboard.walletcharts.forEach(function(arr) {
                                if (maxpg < arr[0]) {
                                    maxpg = arr[0];
                                }
                            });
                            chart_wallet_2 = bb.generate({
                                data: {
                                    columns: data.items[0].billboard.walletcharts,
                                    type: 'donut', // for ESM specify as: donut()
                                },
                                colors: {
                                    'Market Cost': '#ff0000',
                                    'Production Cost': '#ff0001',
                                    'Misc. Costs': '#ff0002',
                                    'Earns': '#00ff00',
                                },
                                bindto: '#walletChartYear',
                            });
                        } else {
                            $('#walletChartContainerYear').hide();
                        }

                        // Ratting Bar
                        if (data.items[0].billboard.rattingbar) {
                            var pgs = [];
                            data.items[0].billboard.rattingbar.forEach(function(arr) {
                                if (arr[0] != 'x') {
                                    pgs.push(arr[0]);
                                }
                            });
                            rattingBar_2 = bb.generate({
                                data: {
                                    x: 'x',
                                    columns: data.items[0].billboard.rattingbar,
                                    type: 'bar', // for ESM specify as: donut()
                                    groups: [pgs],
                                },
                                axis: {
                                    x: {
                                        padding: { right: 8000*60*60*12 },
                                        type: 'timeseries',
                                        tick: { format: '%Y-%m', rotate: 45 }
                                    },
                                    y: {
                                        tick: { format: function(x) {
                                            return d3.format(',')(x);
                                        } },
                                        label: 'ISK'
                                    },
                                },
                                bindto: '#rattingBarYear'
                            });
                        } else {
                            $('#rattingBarContainerYear').hide();
                        }

                        if (data.items[0].billboard.workflowgauge) {
                            var maxpg2 = 0;
                            data.items[0].billboard.workflowgauge.forEach(function(arr) {
                                if (maxpg2 < arr[0]) {
                                    maxpg2 = arr[0];
                                }
                            });
                            gauge_2 = bb.generate({
                                data: {
                                    columns: data.items[0].billboard.workflowgauge,
                                    type: 'gauge', // for ESM specify as: gauge()
                                },
                                bindto: '#workGaugeYear'
                            });
                        } else {
                            $('#workGaugeContainerYear').hide();
                        }

                        return data.items[0].ratting;
                    },
                    cache: false
                },
                'processing': true,
                columns: [
                    {
                        data: 'main_name',
                        render: function (data, type, row) {
                            var imageHTML = '<img src="https://images.evetech.net/characters/' + row.main_id + '/portrait?size=32" class="rounded-circle" title="' + data + '" height="30">';
                            return imageHTML + ' ' + data;
                        }
                    },
                    {   data: 'total_amount',
                        render: function (data, type, row) {
                            // Rückgabe des formatierten Strings mit Farbe und Einheit
                            if (type === 'display') {
                                return formatAndColor(data);
                            }
                            return data;
                        }
                    },
                    {   data: 'total_amount_ess',
                        render: function (data, type, row) {
                            // Rückgabe des formatierten Strings mit Farbe und Einheit
                            if (type === 'display') {
                                return formatAndColor(data);
                            }
                            return data;
                        }
                    },
                    {   data: 'total_amount_mining',
                        render: function (data, type, row) {
                            // Rückgabe des formatierten Strings mit Farbe und Einheit
                            if (type === 'display') {
                                return formatAndColor(data);
                            }
                            return data;
                        }
                    },
                    {   data: 'total_amount_others',
                        render: function (data, type, row) {
                            // Rückgabe des formatierten Strings mit Farbe und Einheit
                            if (type === 'display') {
                                return formatAndColor(data);
                            }
                            return data;
                        }
                    },
                    // Add more columns as needed
                    {
                        data: 'col-total-action',
                        render: function (data, type, row) {
                            return '<button class="btn btn-sm btn-info btn-square" ' +
                                'data-bs-toggle="modal" ' +
                                'data-bs-target="#modalViewCharacterContainer" ' +
                                'aria-label="' + row.main_name + '" ' +
                                'data-ajax_url="/ledger/api/account/'+ row.main_id + '/ledger/template/year/' + currentYear + '/month/0/" ' +
                                'title="' + row.main_name + '">' +
                                '<span class="fas fa-info"></span>' +
                                '</button>';
                        }
                    },
                ],
                order: [[2, 'desc']],
                autoWidth: false,
                columnDefs: [
                    { sortable: false, targets: [5] },
                ],
                footerCallback: function (row, data, start, end, display) {
                    var totalAmountAllChars_year = parseFloat(total_amount);
                    var totalEssAmountAllChars_year = parseFloat(total_amount_ess);
                    var totalMiningAmountAllChars_year = parseFloat(total_amount_mining);
                    var totalOthersAmountAllChars_year = parseFloat(total_amount_others);
                    var totalCombinedAmountAllChars_year = parseFloat(total_amount_combined);

                    $('#foot-year .col-total-amount').html('' + formatAndColor(totalAmountAllChars_year) + '');
                    $('#foot-year .col-total-ess').html('' + formatAndColor(totalEssAmountAllChars_year) + '');
                    $('#foot-year .col-total-mining').html('' + formatAndColor(totalMiningAmountAllChars_year) + '');
                    $('#foot-year .col-total-others').html('' + formatAndColor(totalOthersAmountAllChars_year) + '');
                    $('#foot-year .col-total-gesamt').html('' + formatAndColor(totalCombinedAmountAllChars_year) + '');
                    $('#foot-year .col-total-button').html('<button class="btn btn-sm btn-info btn-square" data-bs-toggle="modal" data-bs-target="#modalViewCharacterContainer"' +
                    'aria-label="{{ data.main_name }}"' +
                    'data-ajax_url="/ledger/api/account/0/ledger/template/year/' + currentYear + '/month/0/" ' +
                    'title="{{ data.main_name }}"> <span class="fas fa-info"></span></button>');
                },
            });
            yearTableInitialized = true;
        }
    });
});

$('#ledger-ratting').on('click', 'a[data-bs-toggle=\'tab\']', function () {
    if (rattingBar_1){
        rattingBar_1.resize({height: 320});
    }
    if (chart_wallet_1){
        chart_wallet_1.resize({height: 320});
    }
    if (gauge_1){
        gauge_1.resize({height: 180});
    }
    if (rattingBar_2 && chart_wallet_2 && gauge_2) {
        rattingBar_2.resize({height: 320});
        chart_wallet_2.resize({height: 320});
        gauge_2.resize({height: 180});
    }
});
