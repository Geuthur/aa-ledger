var total_amount, total_amount_ess, total_amount_combined;
var yearTableInitialized = false;  // Flag to check if the year DataTable is initialized
var chart_1, chart_2, rattingBar_1, rattingBar_2;
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
        var url = '/ledger/api/corporation/0/ledger/year/' + selectedYear + '/month/' + selectedMonth + '/';

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
            url: '/ledger/api/corporation/0/ledger/year/' + currentYear + '/month/' + selectedMonth + '/',
            dataSrc: function (data) {
                // Zusätzliche Daten im DataTable-Objekt speichern
                total_amount = data.items[0].total.total_amount;
                total_amount_ess = data.items[0].total.total_amount_ess;
                total_amount_combined = data.items[0].total.total_amount_all;

                // Billboard
                if (data.items[0].billboard.charts) {
                    $('#ChartContainer').show(); // Container anzeigen, wenn Daten vorhanden sind
                    var maxpg = 0;
                    data.items[0].billboard.charts.forEach(function (arr) {
                        if (maxpg < arr[0]) {
                            maxpg = arr[0];
                        }
                    });
                    if (chart_1) {
                        chart_1.load({
                            columns: data.items[0].billboard.charts,
                            unload: charts_1_cache,
                            done: function() {
                                charts_1_cache = data.items[0].billboard.charts;
                            },
                            resizeAfter: true,
                        });
                    } else {
                        var charts_1_cache = data.items[0].billboard.charts;
                        chart_1 = bb.generate({
                            data: {
                                columns: data.items[0].billboard.charts,
                                type: 'donut'
                            },
                            bindto: '#rattingChart'
                        });
                    }
                } else {
                    $('#ChartContainer').hide(); // Container verstecken, wenn keine Daten vorhanden sind
                }

                // RattingBar
                if (data.items[0].billboard.rattingbar) {
                    $('#rattingBarContainer').show(); // Container anzeigen, wenn Daten vorhanden sind
                    var pgs = data.items[0].billboard.rattingbar.filter(arr => arr[0] !== 'x').map(arr => arr[0]);
                    if (rattingBar_1) {
                        rattingBar_1.load({
                            columns: data.items[0].billboard.rattingbar,
                            groups: [pgs],
                            unload: rattingbar_1_cache,
                            done: function() {
                                rattingbar_1_cache = data.items[0].billboard.rattingbar;
                            },
                            resizeAfter: true,
                        });
                    } else {
                        var rattingbar_1_cache = data.items[0].billboard.rattingbar;
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
            // Add more columns as needed
            {
                data: 'col-total-action',
                render: function (data, type, row) {
                    return '<button class="btn btn-sm btn-info btn-square" ' +
                            'data-bs-toggle="modal" ' +
                            'data-bs-target="#modalViewCharacterContainer" ' +
                            'aria-label="' + row.main_name + '" ' +
                            'data-ajax_url="/ledger/api/corporation/'+ row.main_id + '/ledger/template/year/' + currentYear + '/month/' + selectedMonth + '/" ' +
                            'title="' + row.main_name + '">' +
                            '<span class="fas fa-info"></span>' +
                            '</button>';
                }
            },
        ],
        order: [[1, 'desc']],
        columnDefs: [
            { sortable: false, targets: [3] },
        ],
        footerCallback: function (row, data, start, end, display) {
            var totalAmountAllChars = parseFloat(total_amount);
            var totalEssAmountAllChars = parseFloat(total_amount_ess);
            var totalCombinedAmountAllChars = parseFloat(total_amount_combined);
            $('#foot .col-total-amount').html('' + formatAndColor(totalAmountAllChars) + '');
            $('#foot .col-total-ess').html('' + formatAndColor(totalEssAmountAllChars) + '');
            $('#foot .col-total-gesamt').html('' + formatAndColor(totalCombinedAmountAllChars) + '');
            $('#foot .col-total-button').html('<button class="btn btn-sm btn-info btn-square" data-bs-toggle="modal" data-bs-target="#modalViewCharacterContainer"' +
                'aria-label="{{ data.main_name }}"' +
                'data-ajax_url="/ledger/api/corporation/0/ledger/template/year/' + currentYear + '/month/' + selectedMonth + '/" ' +
                'title="{{ data.main_name }}"> <span class="fas fa-info"></span></button>');
        },
    });

    $('a[data-bs-toggle="tab"]').on('shown.bs.tab', function (e) {
        // Get the id of the tab that was clicked
        var targetTabId = $(e.target).attr('href');

        // Check if the clicked tab is the one containing the year DataTable
        if (targetTabId === '#tab-all_month' && !yearTableInitialized) {

            // Initialisiere DataTable für den Hauptinhalt
            // eslint-disable-next-line no-undef
            YearTable = $('#ratting_year').DataTable({
                ajax: {
                    url: '/ledger/api/corporation/0/ledger/year/' + currentYear + '/month/0/',
                    dataSrc: function (data) {
                        // Zusätzliche Daten im DataTable-Objekt speichern
                        total_amount = data.items[0].total.total_amount;
                        total_amount_ess = data.items[0].total.total_amount_ess;
                        total_amount_combined = data.items[0].total.total_amount_all;

                        // Billboard
                        if (data.items[0].billboard.charts) {
                            $('#ChartYearContainer').show(); // Container anzeigen, wenn Daten vorhanden sind
                            var maxpg = 0;
                            data.items[0].billboard.charts.forEach(function (arr) {
                                if (maxpg < arr[0]) {
                                    maxpg = arr[0];
                                }
                            });
                            if (chart_2) {
                                chart_2.load({
                                    columns: data.items[0].billboard.charts,
                                    unload: charts_2_cache,
                                    done: function() {
                                        charts_2_cache = data.items[0].billboard.charts;
                                    },
                                    resizeAfter: false  // will resize after load
                                });
                            } else {
                                var charts_2_cache = data.items[0].billboard.charts;
                                chart_2 = bb.generate({
                                    data: {
                                        columns: data.items[0].billboard.charts,
                                        type: 'donut'
                                    },
                                    donut: {
                                        title: ''
                                    },
                                    bindto: '#rattingChartYear'
                                });
                            }
                        } else {
                            $('#ChartYearContainer').hide(); // Container verstecken, wenn keine Daten vorhanden sind
                        }

                        // RattingBar
                        if (data.items[0].billboard.rattingbar) {
                            $('#rattingBarYearContainer').show(); // Container anzeigen, wenn Daten vorhanden sind
                            var pgs = data.items[0].billboard.rattingbar.filter(arr => arr[0] !== 'x').map(arr => arr[0]);
                            if (rattingBar_2) {
                                rattingBar_2.load({
                                    columns: data.items[0].billboard.rattingbar,
                                    unload: rattingbar_2_cache,
                                    done: function() {
                                        rattingbar_2_cache = data.items[0].billboard.rattingbar;
                                    },
                                    resizeAfter: false  // will resize after load
                                });
                            } else {
                                var rattingbar_2_cache = data.items[0].billboard.rattingbar;
                                rattingBar_2 = bb.generate({
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
                                    bindto: '#rattingBarYear',
                                });
                            }
                        } else {
                            $('#rattingBarYearContainer').hide(); // Container verstecken, wenn keine Daten vorhanden sind
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
                    // Add more columns as needed
                    {
                        data: 'col-total-action',
                        render: function (data, type, row) {
                            return '<button class="btn btn-sm btn-info btn-square" ' +
                                'data-bs-toggle="modal" ' +
                                'data-bs-target="#modalViewCharacterContainer" ' +
                                'aria-label="' + row.main_name + '" ' +
                                'data-ajax_url="/ledger/api/corporation/'+ row.main_id + '/ledger/template/year/' + currentYear + '/month/0/" ' +
                                'title="' + row.main_name + '">' +
                                '<span class="fas fa-info"></span>' +
                                '</button>';
                        }
                    },
                ],
                order: [[1, 'desc']],
                columnDefs: [
                    { sortable: false, targets: [3] },
                ],
                footerCallback: function (row, data, start, end, display) {
                    var totalAmountAllChars = parseFloat(total_amount);
                    var totalEssAmountAllChars = parseFloat(total_amount_ess);
                    var totalCombinedAmountAllChars = parseFloat(total_amount_combined);
                    $('#foot-year .col-total-amount').html('' + formatAndColor(totalAmountAllChars) + '');
                    $('#foot-year .col-total-ess').html('' + formatAndColor(totalEssAmountAllChars) + '');
                    $('#foot-year .col-total-gesamt').html('' + formatAndColor(totalCombinedAmountAllChars) + '');
                    $('#foot-year .col-total-button').html('<button class="btn btn-sm btn-info btn-square" data-bs-toggle="modal" data-bs-target="#modalViewCharacterContainer"' +
                    'aria-label="{{ data.main_name }}"' +
                    'data-ajax_url="/ledger/api/corporation/0/ledger/template/year/' + currentYear + '/month/0/" ' +
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
    if (chart_1){
        chart_1.resize({height: 320});
    }
    if (rattingBar_2 && chart_2) {
        rattingBar_2.resize({height: 320});
        chart_2.resize({height: 320});
    }
});
