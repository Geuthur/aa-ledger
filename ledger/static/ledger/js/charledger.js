
var total_amount, total_amount_ess, total_amount_mining, total_amount_others, total_amount_combined, total_amount_costs;
var selectedMonth, selectedYear, monthText, yearText;
var MonthTable, YearTable;
var bb, d3;
var BillboardMonth, BillboardYear, BillboardHourly;
// eslint-disable-next-line no-undef
var characterPk = charactersettings.character_pk;

// Aktuelles Datumobjekt erstellen
var currentDate = new Date();

// Aktuelles Jahr und Monat abrufen
selectedYear = currentDate.getFullYear();
selectedMonth = currentDate.getMonth() + 1;
monthText = getMonthName(selectedMonth);

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
    showLoading('Month');
    hideContainer('Month');

    MonthTable.clear().draw();
    $('#foot').hide();

    selectedMonth = $(this).find('a').data('bs-month-id');
    monthText = getMonthName(selectedMonth);

    // URL für die Daten der ausgewählten Kombination von Jahr und Monat erstellen
    var newurl = '/ledger/api/account/' + characterPk + '/ledger/year/' + selectedYear + '/month/' + selectedMonth + '/';

    // DataTable neu laden mit den Daten des ausgewählten Monats
    reloadMonthAjax(newurl);
    $('#currentMonthLink').text('Month - ' + monthText);
});

$('#yearDropdown li').click(function() {
    showLoading('Year');
    showLoading('Month');
    hideContainer('Year');
    hideContainer('Month');

    YearTable.clear().draw();
    $('#foot-year').hide();
    MonthTable.clear().draw();
    $('#foot').hide();

    selectedYear = $(this).text();

    // URL für die Daten der ausgewählten Kombination von Jahr und Monat erstellen
    var newurl = '/ledger/api/account/' + characterPk + '/ledger/year/' + selectedYear + '/month/' + selectedMonth + '/';
    var newurl_year = '/ledger/api/account/' + characterPk + '/ledger/year/' + selectedYear + '/month/0/';

    // DataTable neu laden mit den Daten des ausgewählten Monats
    reloadMonthAjax(newurl);
    reloadYearAjax(newurl_year);
    $('#currentMonthLink').text('Month - ' + monthText);
    $('#currentYearLink').text('Year - ' + selectedYear);
});

$('#barDropdown-Month li').click(function() {
    var selectedMode = $(this).text();
    if (selectedMode === 'Hourly') {
        updateBillboard(BillboardHourly, 'Month', 'Hourly');
    } else {
        updateBillboard(BillboardMonth, 'Month');
    }
});

function hideLoading(id) {
    $('#bar-loading-'+id).addClass('d-none');
    $('#chart-loading-'+id).addClass('d-none');
    $('#loadingIndicator-'+id).addClass('d-none');
}

function showLoading(id) {
    $('#bar-loading-'+id).removeClass('d-none');
    $('#chart-loading-'+id).removeClass('d-none');
    $('#loadingIndicator-'+id).removeClass('d-none');
}

function hideContainer(id) {
    $('#ChartContainer-'+id).addClass('d-none');
    $('#rattingBarContainer-'+id).addClass('d-none');
    $('#workGaugeContainer-'+id).addClass('d-none');
}

function showContainer(id) {
    $('#ChartContainer-'+id).removeClass('d-none');
    $('#rattingBarContainer-'+id).removeClass('d-none');
    $('#workGaugeContainer-'+id).removeClass('d-none');
}

function reloadMonthAjax(newUrl) {
    MonthAjax.url = newUrl; // Update URL
    $('#ratting').DataTable().destroy();
    $.ajax(MonthAjax);
}

var MonthAjax = {
    url: '/ledger/api/account/' + characterPk + '/ledger/year/' + selectedYear + '/month/' + selectedMonth + '/',
    type: 'GET',
    success: function(data) {
        hideLoading('Month');
        total_amount = data[0].total.total_amount;
        total_amount_ess = data[0].total.total_amount_ess;
        total_amount_others = data[0].total.total_amount_others;
        total_amount_mining = data[0].total.total_amount_mining;
        total_amount_combined = data[0].total.total_amount_all;
        total_amount_costs = data[0].total.total_amount_costs;
        BillboardMonth = data[0].billboard.standard;
        BillboardHourly = data[0].billboard.hourly;

        MonthTable = $('#ratting').DataTable({
            data: data[0].ratting,
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
                {   data: 'total_amount_mining',
                    render: function (data, type, row) {
                        if (type === 'display') {
                            return formatAndColor(data);
                        }
                        return data;
                    }
                },
                {   data: 'total_amount_others',
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
                        'data-ajax_url="/ledger/api/account/'+ row.main_id + '/ledger/template/year/' + selectedYear + '/month/' + selectedMonth + '/" ' +
                        'title="' + row.main_name + '">' +
                        '<span class="fas fa-info"></span>' +
                        '</button>';
                    }
                },
            ],
            order: [[1, 'desc']],
            columnDefs: [
                {
                    sortable: false,
                    targets: [5],
                    className: 'text-end',
                },
            ],
            footerCallback: function (row, data, start, end, display) {
                var totalAmountAllChars = parseFloat(total_amount);
                var totalEssAmountAllChars = parseFloat(total_amount_ess);
                var totalMiningAmountAllChars = parseFloat(total_amount_mining);
                var totalOthersAmountAllChars = parseFloat(total_amount_others);
                var totalCombinedAmountAllChars = parseFloat(total_amount_combined);
                var totalCostsAmountAllChars = parseFloat(total_amount_costs);
                $('#foot .col-total-amount').html('' + formatAndColor(totalAmountAllChars) + '');
                $('#foot .col-total-ess').html('' + formatAndColor(totalEssAmountAllChars) + '');
                $('#foot .col-total-mining').html('' + formatAndColor(totalMiningAmountAllChars) + '');
                $('#foot .col-total-others').html('' + formatAndColor(totalOthersAmountAllChars) + '');
                $('#foot .col-total-gesamt').html('' + formatAndColor(totalCombinedAmountAllChars) + '');
                $('#foot .col-total-costs').html('' + formatAndColor(totalCostsAmountAllChars) + '');
                $('#foot .col-total-button').html('<button class="btn btn-sm btn-info btn-square" data-bs-toggle="modal" data-bs-target="#modalViewCharacterContainer"' +
                    'aria-label="{{ data.main_name }}"' +
                    'data-ajax_url="/ledger/api/account/' + characterPk + '/ledger/template/year/' + selectedYear + '/month/' + selectedMonth + '/" ' +
                    'title="{{ data.main_name }}"> <span class="fas fa-info"></span></button>')
                    .addClass('text-end');
            },
            initComplete: function(settings, json) {
                if ($('#currentMonthLink').hasClass('active')) {
                    loadBillboard(BillboardMonth, 'Month');
                }
                $('#foot').show();
            }
        });
    },
    error: function(xhr, status, error) {
        if (xhr.status === 403) {
            hideLoading('Month');
            $('#ratting').hide();
            $('#errorHandler').removeClass('d-none');
            $('.dropdown-toggle').attr('disabled', true);
        }
    }
};

function reloadYearAjax(newUrl) {
    YearAjax.url = newUrl; // Update URL
    $('#ratting_year').DataTable().destroy();
    $.ajax(YearAjax);
}

var YearAjax = {
    url: '/ledger/api/account/' + characterPk + '/ledger/year/' + selectedYear + '/month/0/',
    type: 'GET',
    success: function(data) {
        hideLoading('Year');
        // Zusätzliche Daten im DataTable-Objekt speichern
        total_amount = data[0].total.total_amount;
        total_amount_ess = data[0].total.total_amount_ess;
        total_amount_mining = data[0].total.total_amount_mining;
        total_amount_others = data[0].total.total_amount_others;
        total_amount_combined = data[0].total.total_amount_all;
        total_amount_costs = data[0].total.total_amount_costs;
        BillboardYear = data[0].billboard.standard;

        YearTable = $('#ratting_year').DataTable({
            data: data[0].ratting,
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
                {   data: 'total_amount_mining',
                    render: function (data, type, row) {
                        if (type === 'display') {
                            return formatAndColor(data);
                        }
                        return data;
                    }
                },
                {   data: 'total_amount_others',
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
                        'data-ajax_url="/ledger/api/account/'+ row.main_id + '/ledger/template/year/' + selectedYear + '/month/0/" ' +
                        'title="' + row.main_name + '">' +
                        '<span class="fas fa-info"></span>' +
                        '</button>';
                    }
                },
            ],
            order: [[1, 'desc']],
            columnDefs: [
                {
                    sortable: false,
                    targets: [5],
                    className: 'text-end',
                },
            ],
            footerCallback: function (row, data, start, end, display) {
                var totalAmountAllChars_year = parseFloat(total_amount);
                var totalEssAmountAllChars_year = parseFloat(total_amount_ess);
                var totalMiningAmountAllChars_year = parseFloat(total_amount_mining);
                var totalOthersAmountAllChars_year = parseFloat(total_amount_others);
                var totalCombinedAmountAllChars_year = parseFloat(total_amount_combined);
                var totalCostsAmountAllChars_year = parseFloat(total_amount_costs);

                $('#foot-year .col-total-amount').html('' + formatAndColor(totalAmountAllChars_year) + '');
                $('#foot-year .col-total-ess').html('' + formatAndColor(totalEssAmountAllChars_year) + '');
                $('#foot-year .col-total-mining').html('' + formatAndColor(totalMiningAmountAllChars_year) + '');
                $('#foot-year .col-total-others').html('' + formatAndColor(totalOthersAmountAllChars_year) + '');
                $('#foot-year .col-total-gesamt').html('' + formatAndColor(totalCombinedAmountAllChars_year) + '');
                $('#foot-year .col-total-costs').html('' + formatAndColor(totalCostsAmountAllChars_year) + '');
                $('#foot-year .col-total-button').html('<button class="btn btn-sm btn-info btn-square" data-bs-toggle="modal" data-bs-target="#modalViewCharacterContainer"' +
                'aria-label="{{ data.main_name }}"' +
                'data-ajax_url="/ledger/api/account/' + characterPk + '/ledger/template/year/' + selectedYear + '/month/0/" ' +
                'title="{{ data.main_name }}"> <span class="fas fa-info"></span></button>')
                    .addClass('text-end');
            },
            initComplete: function(settings, json) {
                if ($('#currentYearLink').hasClass('active')) {
                    loadBillboard(BillboardYear, 'Year');
                }
                $('#foot-year').show();
            }
        });
    },
    error: function(xhr, status, error) {
        if (xhr.status === 403) {
            hideLoading('Year');
            $('#ratting_year').hide();
            $('#errorHandler-Year').removeClass('d-none');
            $('.dropdown-toggle').attr('disabled', true);
        }
    }
};

function loadBillboard(data, id) {
    // Initialize a charts object if it doesn't exist
    if (window.charts === undefined) {
        window.charts = {};
    }

    // Billboard
    if (data.walletcharts) {
        $('#ChartContainer-' + id).removeClass('d-none');
        var maxpg = 0;
        data.walletcharts.forEach(function (arr) {
            if (maxpg < arr[0]) {
                maxpg = arr[0];
            }
        });
        // Store the chart in the charts object using id as the key
        window.charts['chart' + id] = bb.generate({
            data: {
                columns: data.walletcharts,
                type: 'donut'
            },
            donut: {
                title: ''
            },
            bindto: '#rattingChart-' + id,
            legend: {
                show: true
            }
        });
    } else {
        $('#ChartContainer-'+id).addClass('d-none');
    }

    // Initialize a bar object if it doesn't exist
    if (window.bar === undefined) {
        window.bar = {};
    }

    // Ratting Bar
    if (data.rattingbar) {
        $('#rattingBarContainer-' + id).removeClass('d-none');
        // ---- Stacks Bar Optional ----
        //var pgs = [];
        //data.rattingbar.forEach(function(arr) {
        //    if (arr[0] != 'x') {
        //        pgs.push(arr[0]);
        //    }
        //});
        window.bar['bar' + id] = bb.generate({
            data: {
                x: 'x',
                columns: data.rattingbar,
                type: 'bar',
                // groups: [pgs],
            },
            axis: {
                x: {
                    padding: { right: 8000*60*60*12 },
                    type: 'timeseries',
                    tick: {
                        format: '%Y-%m' + (id === 'Month' ? '-%d' : ''),
                        rotate: 45
                    }
                },
                y: {
                    tick: { format: function(x) {
                        return d3.format(',')(x);
                    } },
                    label: 'ISK'
                },
            },
            bindto: '#rattingBar-'+id,
            legend: {
                show: true
            }
        });
    } else {
        $('#rattingBarContainer-'+id).addClass('d-none');
    }

    // Initialize a gauge object if it doesn't exist
    if (window.gauge === undefined) {
        window.gauge = {};
    }

    // Workflow Gauge
    if (data.workflowgauge) {
        $('#workGaugeContainer-' + id).removeClass('d-none');
        var maxpg2 = 0;
        data.workflowgauge.forEach(function(arr) {
            if (maxpg2 < arr[0]) {
                maxpg2 = arr[0];
            }
        });
        window.gauge['gauge' + id] = bb.generate({
            data: {
                columns: data.workflowgauge,
                type: 'gauge'
            },
            bindto: '#rattingworkGauge-'+id,
            legend: {
                show: true
            }
        });
    } else {
        $('#workGaugeContainer-'+id).addClass('d-none');
    }
}

function updateBillboard(data, id, selectedMode) {
    // Update Bar Chart
    if (data.rattingbar && window.bar && window.bar['bar' + id]) {
        window.bar['bar' + id].unload();

        // Berechnen des maximalen Werts für die Y-Achse
        let maxYValue = Math.max(...data.rattingbar.map(d => Math.max(...d.slice(1))));

        // Anpassen der maxYValue für eine bessere Darstellung
        maxYValue += maxYValue * 0.1; // Fügt 10% Puffer hinzu

        window.bar['bar' + id].load({
            columns: data.rattingbar,
            axis: {
                x: {
                    padding: { right: 8000*60*60*12 },
                    type: 'timeseries',
                    tick: {
                        format: '%Y-%m' + (id === 'Month' ? '-%d' : '') + (selectedMode === 'Hourly' ? ' %H' : ''),
                        rotate: 45
                    }
                },
                y: {
                    tick: { format: function(x) { return d3.format(',')(x); } },
                    label: 'ISK',
                    max: maxYValue, // Setzt die maximale Y-Achse dynamisch
                },
            },
            bar: {
                width: {
                    ratio: 0.9,
                    max: 30
                }
            },
        });
    }
}

document.addEventListener('DOMContentLoaded', function () {
    // Initialize DataTable
    $.ajax(MonthAjax);
    $.ajax(YearAjax);
});

$('#ledger-ratting').on('click', 'a[data-bs-toggle=\'tab\']', function () {
    // Warten, um sicherzustellen, dass das Tab gewechselt hat
    setTimeout(function() {
        // Überprüfen, ob das spezifische Tab aktiv ist
        if ($('#currentYearLink').hasClass('active')) {
            loadBillboard(BillboardYear, 'Year');
        }
    }, 500);
    setTimeout(function() {
        // Überprüfen, ob das spezifische Tab aktiv ist
        if ($('#currentMonthLink').hasClass('active')) {
            loadBillboard(BillboardMonth, 'Month');
        }
    }, 500);
});
