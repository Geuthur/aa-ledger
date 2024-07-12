var total_amount, total_amount_ess, total_amount_combined;
var selectedMonth, selectedYear, monthText, yearText;
var MonthTable, YearTable;
var bb, d3;
var AjaxDatMonth, AjaxDataYear;
// eslint-disable-next-line no-undef
var corporationPk = corporationsettings.corporation_pk;

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
    var newurl = '/ledger/api/corporation/' + corporationPk + '/ledger/year/' + selectedYear + '/month/' + selectedMonth + '/';

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
    var newurl = '/ledger/api/corporation/' + corporationPk + '/ledger/year/' + selectedYear + '/month/' + selectedMonth + '/';
    var newurl_year = '/ledger/api/corporation/' + corporationPk + '/ledger/year/' + selectedYear + '/month/0/';

    // DataTable neu laden mit den Daten des ausgewählten Monats
    reloadMonthAjax(newurl);
    reloadYearAjax(newurl_year);
    $('#currentMonthLink').text('Month - ' + monthText);
    $('#currentYearLink').text('Year - ' + selectedYear);
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
}

function showContainer(id) {
    $('#ChartContainer-'+id).removeClass('d-none');
    $('#rattingBarContainer-'+id).removeClass('d-none');
}

function reloadMonthAjax(newUrl) {
    MonthAjax.url = newUrl; // Update URL
    $('#ratting').DataTable().destroy();
    $.ajax(MonthAjax);
}

var MonthAjax = {
    url: '/ledger/api/corporation/' + corporationPk + '/ledger/year/' + selectedYear + '/month/' + selectedMonth + '/',
    type: 'GET',
    success: function(data) {
        hideLoading('Month');
        total_amount = data[0].total.total_amount;
        total_amount_ess = data[0].total.total_amount_ess;
        total_amount_combined = data[0].total.total_amount_all;
        AjaxDatMonth = data[0];

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
            initComplete: function(settings, json) {
                if ($('#currentMonthLink').hasClass('active')) {
                    loadBillboard(AjaxDatMonth, 'Month');
                }
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
    url: '/ledger/api/corporation/' + corporationPk + '/ledger/year/' + selectedYear + '/month/0/',
    type: 'GET',
    success: function(data) {
        hideLoading('Year');
        // Zusätzliche Daten im DataTable-Objekt speichern
        total_amount = data[0].total.total_amount;
        total_amount_ess = data[0].total.total_amount_ess;
        total_amount_combined = data[0].total.total_amount_all;
        AjaxDataYear = data[0];

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
            initComplete: function(settings, json) {
                if ($('#currentYearLink').hasClass('active')) {
                    loadBillboard(AjaxDataYear, 'Year');
                }
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
    if (data.billboard.charts) {
        $('#ChartContainer-' + id).removeClass('d-none');
        var maxpg = 0;
        data.billboard.charts.forEach(function (arr) {
            if (maxpg < arr[0]) {
                maxpg = arr[0];
            }
        });
        // Store the chart in the charts object using id as the key
        window.charts['chart' + id] = bb.generate({
            data: {
                columns: data.billboard.charts,
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

    // Initialize a charts object if it doesn't exist
    if (window.bar === undefined) {
        window.bar = {};
    }

    // Ratting Bar
    if (data.billboard.rattingbar) {
        $('#rattingBarContainer-' + id).removeClass('d-none');
        var pgs = [];
        data.billboard.rattingbar.forEach(function(arr) {
            if (arr[0] != 'x') {
                pgs.push(arr[0]);
            }
        });
        window.bar['bar' + id] = bb.generate({
            data: {
                x: 'x',
                columns: data.billboard.rattingbar,
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
            bindto: '#rattingBar-'+id,
            legend: {
                show: true
            }
        });
    } else {
        $('#rattingBarContainer-'+id).addClass('d-none');
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
            loadBillboard(AjaxDataYear, 'Year');
        }
    }, 500);
    setTimeout(function() {
        // Überprüfen, ob das spezifische Tab aktiv ist
        if ($('#currentMonthLink').hasClass('active')) {
            loadBillboard(AjaxDatMonth, 'Month');
        }
    }, 500);
});
