var total_amount, total_amount_ess, total_amount_combined;
var yearTableInitialized = false;
var chart_1, chart_2, rattingBar_1, rattingBar_2;
var selectedMonth, selectedYear, monthText, yearText;
var MonthTable, YearTable;
var bb, d3;
// eslint-disable-next-line no-undef
var corporationPk = corporationsettings.corporation_pk;

// Aktuelles Datumobjekt erstellen
var currentDate = new Date();

// Aktuelles Jahr und Monat abrufen
selectedYear = currentDate.getFullYear();
selectedMonth = currentDate.getMonth() + 1;
monthText = getMonthName(selectedMonth);

function resizeCharts() {
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
}

function getMonthName(monthNumber) {
    var months = ['January', 'February', 'March', 'April', 'May', 'June',
        'July', 'August', 'September', 'October', 'November', 'December'];
    return months[monthNumber - 1]; // Array ist 0-basiert, daher -1
}

// Function to format currency and apply color
function formatAndColor(value) {
    // Formatieren und Komma-Stellen entfernen
    var formattedValue = new Intl.NumberFormat('de-DE', { minimumFractionDigits: 0, maximumFractionDigits: 0 }).format(value);

    // Bestimme die Textfarbe basierend auf dem Wert
    var color = value >= 0 ? 'chartreuse' : 'red';

    // Rückgabe des formatierten Strings mit Farbe und Einheit
    return '<span style="color: ' + color + ';">' + formattedValue + '</span> ISK';
}

$('#monthDropdown li').click(function() {
    selectedMonth = $(this).find('a').data('bs-month-id');
    monthText = getMonthName(selectedMonth);

    // URL für die Daten der ausgewählten Kombination von Jahr und Monat erstellen
    var url = '/ledger/api/corporation/' + corporationPk + '/ledger/year/' + selectedYear + '/month/' + selectedMonth + '/';

    // DataTable neu laden mit den Daten des ausgewählten Monats
    MonthTable.ajax.url(url).load();
    $('#currentMonthLink').text('Month - ' + monthText);
});

$('#yearDropdown li').click(function() {
    if (!$.fn.DataTable.isDataTable('#ratting_year')) {
        initializeYearTable();
    }

    selectedYear = $(this).text();

    // URL für die Daten der ausgewählten Kombination von Jahr und Monat erstellen
    var url = '/ledger/api/corporation/' + corporationPk + '/ledger/year/' + selectedYear + '/month/' + selectedMonth + '/';
    var url_year = '/ledger/api/corporation/' + corporationPk + '/ledger/year/' + selectedYear + '/month/0/';

    // DataTable neu laden mit den Daten des ausgewählten Monats
    MonthTable.ajax.url(url).load();
    YearTable.ajax.url(url_year).load();
    $('#currentMonthLink').text('Month - ' + monthText);
    $('#currentYearLink').text('Year - ' + selectedYear);
});

document.addEventListener('DOMContentLoaded', function () {
    // Initialize DataTable for current_month
    MonthTable = $('#ratting').DataTable({
        ajax: {
            url: '/ledger/api/corporation/' + corporationPk + '/ledger/year/' + selectedYear + '/month/' + selectedMonth + '/',
            dataSrc: function (data) {
                // Zusätzliche Daten im DataTable-Objekt speichern
                total_amount = data[0].total.total_amount;
                total_amount_ess = data[0].total.total_amount_ess;
                total_amount_combined = data[0].total.total_amount_all;

                // Billboard
                if (data[0].billboard.charts) {
                    $('#ChartContainer').show(); // Container anzeigen, wenn Daten vorhanden sind
                    var maxpg = 0;
                    data[0].billboard.charts.forEach(function (arr) {
                        if (maxpg < arr[0]) {
                            maxpg = arr[0];
                        }
                    });
                    if (chart_1) {
                        chart_1.load({
                            columns: data[0].billboard.charts,
                            unload: charts_1_cache,
                            done: function() {
                                charts_1_cache = data[0].billboard.charts;
                            },
                            resizeAfter: true,
                        });
                    } else {
                        var charts_1_cache = data[0].billboard.charts;
                        chart_1 = bb.generate({
                            data: {
                                columns: data[0].billboard.charts,
                                type: 'donut'
                            },
                            bindto: '#rattingChart'
                        });
                    }
                } else {
                    $('#ChartContainer').hide();
                }

                // RattingBar
                if (data[0].billboard.rattingbar) {
                    $('#rattingBarContainer').show();
                    var pgs = data[0].billboard.rattingbar.filter(arr => arr[0] !== 'x').map(arr => arr[0]);
                    if (rattingBar_1) {
                        rattingBar_1.load({
                            columns: data[0].billboard.rattingbar,
                            groups: [pgs],
                            resizeAfter: true,
                        });
                    } else {
                        rattingBar_1 = bb.generate({
                            data: {
                                x: 'x',
                                columns: data[0].billboard.rattingbar,
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
                    $('#rattingBarContainer').hide();
                }

                return data[0].ratting;
            },
            cache: false,
            error: function (xhr, status, error) {
                // Prüfen, ob der Status 403 Forbidden ist
                if (xhr.status === 403) {
                    // Alle Container verstecken
                    $('#ChartContainer').hide();
                    $('#rattingBarContainer').hide();
                    // DataTable leeren und Meldung anzeigen, dass keine Daten vorhanden sind
                    MonthTable.clear().draw();
                    MonthTable.rows.add([{ main_name: 'Keine Daten vorhanden', total_amount: '', total_amount_ess: '', 'col-total-action': '' }]).draw();
                }
            }
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
                    if (type === 'display') {
                        return formatAndColor(data);
                    }
                    return data;
                }
            },
            {   data: 'total_amount_ess',
                render: function (data, type, row) {
                    if (type === 'display') {
                        return formatAndColor(data);
                    }
                    return data;
                }
            },
            {
                data: 'col-total-action',
                render: function (data, type, row) {
                    return '<button class="btn btn-sm btn-info btn-square" ' +
                            'data-bs-toggle="modal" ' +
                            'data-bs-target="#modalViewCharacterContainer" ' +
                            'aria-label="' + row.main_name + '" ' +
                            'data-ajax_url="/ledger/api/corporation/'+ row.main_id + '/ledger/template/year/' + selectedYear + '/month/' + selectedMonth + '/" ' +
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
                'data-ajax_url="/ledger/api/corporation/' + corporationPk + '/ledger/template/year/' + selectedYear + '/month/' + selectedMonth + '/?corp=true" ' +
                'title="{{ data.main_name }}"> <span class="fas fa-info"></span></button>');
        },
    });
});

function initializeYearTable() {
    YearTable = $('#ratting_year').DataTable({
        ajax: {
            url: '/ledger/api/corporation/' + corporationPk + '/ledger/year/' + selectedYear + '/month/0/',
            dataSrc: function (data) {
                // Zusätzliche Daten im DataTable-Objekt speichern
                total_amount = data[0].total.total_amount;
                total_amount_ess = data[0].total.total_amount_ess;
                total_amount_combined = data[0].total.total_amount_all;

                // Billboard
                if (data[0].billboard.charts) {
                    $('#ChartYearContainer').show();
                    var maxpg = 0;
                    data[0].billboard.charts.forEach(function (arr) {
                        if (maxpg < arr[0]) {
                            maxpg = arr[0];
                        }
                    });
                    if (chart_2) {
                        chart_2.load({
                            columns: data[0].billboard.charts,
                            unload: charts_2_cache,
                            done: function() {
                                charts_2_cache = data[0].billboard.charts;
                            },
                            resizeAfter: false  // will resize after load
                        });
                    } else {
                        var charts_2_cache = data[0].billboard.charts;
                        chart_2 = bb.generate({
                            data: {
                                columns: data[0].billboard.charts,
                                type: 'donut'
                            },
                            donut: {
                                title: ''
                            },
                            bindto: '#rattingChartYear'
                        });
                    }
                } else {
                    $('#ChartYearContainer').hide();
                }

                // Ratting Bar
                if (data[0].billboard.rattingbar) {
                    $('#rattingBarContainerYear').show();
                    var pgs = [];
                    data[0].billboard.rattingbar.forEach(function(arr) {
                        if (arr[0] != 'x') {
                            pgs.push(arr[0]);
                        }
                    });
                    rattingBar_2 = bb.generate({
                        data: {
                            x: 'x',
                            columns: data[0].billboard.rattingbar,
                            type: 'bar',
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

                return data[0].ratting;
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
                    if (type === 'display') {
                        return formatAndColor(data);
                    }
                    return data;
                }
            },
            {   data: 'total_amount_ess',
                render: function (data, type, row) {
                    if (type === 'display') {
                        return formatAndColor(data);
                    }
                    return data;
                }
            },
            {
                data: 'col-total-action',
                render: function (data, type, row) {
                    return '<button class="btn btn-sm btn-info btn-square" ' +
                        'data-bs-toggle="modal" ' +
                        'data-bs-target="#modalViewCharacterContainer" ' +
                        'aria-label="' + row.main_name + '" ' +
                        'data-ajax_url="/ledger/api/corporation/'+ row.main_id + '/ledger/template/year/' + selectedYear + '/month/0/" ' +
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
            'data-ajax_url="/ledger/api/corporation/' + corporationPk + '/ledger/template/year/' + selectedYear + '/month/0/?corp=true" ' +
            'title="{{ data.main_name }}"> <span class="fas fa-info"></span></button>');
        },
    });
}

$('#ledger-ratting').on('click', 'a[data-bs-toggle=\'tab\']', function () {
    if (!$.fn.DataTable.isDataTable('#ratting_year')) {
        initializeYearTable();
    } else {
        resizeCharts();
    }
});

$('#monthDropdown li, #yearDropdown li').click(function() {
    resizeCharts();
});
