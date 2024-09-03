/* global corporationsettings */

var ledgerData;
var MonthTable, YearTable;
var bb, d3;
var BillboardMonth, BillboardYear;

var corporationPk = corporationsettings.corporation_pk;

// Aktuelles Datumobjekt erstellen
var currentDate = new Date();

// Aktuelles Jahr und Monat abrufen
var selectedYear = currentDate.getFullYear();
var selectedMonth = currentDate.getMonth() + 1;
var monthText = getMonthName(selectedMonth);

// Billboard URLs
var BillboardUrl = '/ledger/api/corporation/' + corporationPk + '/billboard/year/' + selectedYear + '/month/' + selectedMonth + '/';
var BillboardUrlYear = '/ledger/api/corporation/' + corporationPk + '/billboard/year/' + selectedYear + '/month/0/';

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
    $('#foot-Month').hide();

    selectedMonth = $(this).find('a').data('bs-month-id');
    monthText = getMonthName(selectedMonth);

    // URL für die Daten der ausgewählten Kombination von Jahr und Monat erstellen
    var newurl = '/ledger/api/corporation/' + corporationPk + '/ledger/year/' + selectedYear + '/month/' + selectedMonth + '/';
    var BillboardUrl = '/ledger/api/corporation/' + corporationPk + '/billboard/year/' + selectedYear + '/month/' + selectedMonth + '/';

    // Daten neu laden mit den Daten des ausgewählten Monats
    setBillboardData(BillboardUrl, 'Month');
    reloadAjax(newurl, MonthAjax);
    $('#currentMonthLink').text('Month - ' + monthText);
});

$('#yearDropdown li').click(function() {
    showLoading('Year');
    showLoading('Month');
    hideContainer('Year');
    hideContainer('Month');

    YearTable.clear().draw();
    $('#foot-Year').hide();

    MonthTable.clear().draw();
    $('#foot-Month').hide();

    selectedYear = $(this).text();

    // URL für die Daten der ausgewählten Kombination von Jahr und Monat erstellen
    var newurl = '/ledger/api/corporation/' + corporationPk + '/ledger/year/' + selectedYear + '/month/' + selectedMonth + '/';
    var newurl_year = '/ledger/api/corporation/' + corporationPk + '/ledger/year/' + selectedYear + '/month/0/';
    var BillboardUrl = '/ledger/api/corporation/' + corporationPk + '/billboard/year/' + selectedYear + '/month/' + selectedMonth + '/';
    var BillboardUrlYear = '/ledger/api/corporation/' + corporationPk + '/billboard/year/' + selectedYear + '/month/0/';

    // Daten neu laden mit den Daten des ausgewählten Jahres
    setBillboardData(BillboardUrl, 'Month');
    setBillboardData(BillboardUrlYear, 'Year');
    reloadAjax(newurl, MonthAjax);
    reloadAjax(newurl_year, YearAjax);
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

function reloadAjax(newUrl, ajax) {
    ajax.url = newUrl; // Update URL
    $.ajax(ajax);
}

function setBillboardData(url, id) {
    $.ajax({
        url: url,
        type: 'GET',
        success: function(data) {
            if (id === 'Month') {
                BillboardMonth = data[0].billboard.standard;
                loadBillboard(data[0].billboard.standard, 'Month');
            } else {
                BillboardYear = data[0].billboard.standard;
                loadBillboard(data[0].billboard.standard, 'Year');
            }
        }
    });
}

var MonthAjax = {
    url: '/ledger/api/corporation/' + corporationPk + '/ledger/year/' + selectedYear + '/month/' + selectedMonth + '/',
    type: 'GET',
    success: function(data) {
        if (MonthTable) {
            $('#ratting-Month').DataTable().destroy();
        }
        hideLoading('Month');
        var total_amount = data[0].total.total_amount;
        var total_amount_ess = data[0].total.total_amount_ess;
        var total_amount_combined = data[0].total.total_amount_all;
        // Daten für die Billboard-URLs speichern

        MonthTable = $('#ratting-Month').DataTable({
            data: data[0].ratting,
            columns: [
                {
                    data: 'main_name',
                    render: function (data, type, row) {
                        // Initialize alt_names
                        var alt_portrait = 'Included Characters: ';

                        // Loop through alt_names and add each image
                        row.alt_names.forEach(function(character_id) {
                            alt_portrait += '<img src="https://images.evetech.net/characters/' + character_id + '/portrait?size=32" class="rounded-circle" height="30">';
                        });

                        var imageHTML = '<img src="https://images.evetech.net/characters/' + row.main_id + '/portrait?size=32" class="rounded-circle" height="30" data-bs-trigger="hover" data-bs-toggle="popover" data-bs-content=\''+ alt_portrait +'\' >';
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
                            'data-ajax_url="/ledger/api/corporation/'+ corporationPk +'/character/'+ row.main_id + '/ledger/template/year/' + selectedYear + '/month/' + selectedMonth + '/" ' +
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
                    targets: [3],
                    className: 'text-end',
                },
            ],
            footerCallback: function (row, data, start, end, display) {
                var totalAmountAllChars = parseFloat(total_amount);
                var totalEssAmountAllChars = parseFloat(total_amount_ess);
                var totalCombinedAmountAllChars = parseFloat(total_amount_combined);
                $('#foot-Month .col-total-amount').html('' + formatAndColor(totalAmountAllChars) + '');
                $('#foot-Month .col-total-ess').html('' + formatAndColor(totalEssAmountAllChars) + '');
                $('#foot-Month .col-total-gesamt').html('' + formatAndColor(totalCombinedAmountAllChars) + '');
                $('#foot-Month .col-total-button').html('<button class="btn btn-sm btn-info btn-square" data-bs-toggle="modal" data-bs-target="#modalViewCharacterContainer"' +
                    'data-ajax_url="/ledger/api/corporation/'+ corporationPk +'/character/' + corporationPk + '/ledger/template/year/' + selectedYear + '/month/' + selectedMonth + '/?corp=true" ' +
                    'title="{{ data.main_name }}"> <span class="fas fa-info"></span></button>')
                    .addClass('text-end');
            },
            initComplete: function(settings, json) {
                $('#foot-Month').show();
                // Initialize popover
                var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
                var popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
                    // eslint-disable-next-line no-undef
                    return new bootstrap.Popover(popoverTriggerEl, {
                        html: true
                    });
                });
            }
        });
    },
    error: function(xhr, status, error) {
        if (xhr.status === 403) {
            hideLoading('Month');
            $('#ratting-Month').hide();
            $('#errorHandler').removeClass('d-none');
            $('.dropdown-toggle').attr('disabled', true);
        }
    }
};

var YearAjax = {
    url: '/ledger/api/corporation/' + corporationPk + '/ledger/year/' + selectedYear + '/month/0/',
    type: 'GET',
    success: function(data) {
        if (YearTable) {
            $('#ratting-Year').DataTable().destroy();
        }
        hideLoading('Year');
        // Zusätzliche Daten im DataTable-Objekt speichern
        var total_amount = data[0].total.total_amount;
        var total_amount_ess = data[0].total.total_amount_ess;
        var total_amount_combined = data[0].total.total_amount_all;

        // DataTable neu initialisieren
        YearTable = $('#ratting-Year').DataTable({
            data: data[0].ratting,
            columns: [
                {
                    data: 'main_name',
                    render: function (data, type, row) {
                    // Initialize alt_names
                        var alt_portrait = 'Included Characters: ';

                        // Loop through alt_names and add each image
                        row.alt_names.forEach(function(character_id) {
                            alt_portrait += '<img src="https://images.evetech.net/characters/' + character_id + '/portrait?size=32" class="rounded-circle" height="30">';
                        });

                        var imageHTML = '<img src="https://images.evetech.net/characters/' + row.main_id + '/portrait?size=32" class="rounded-circle" height="30" data-bs-trigger="hover" data-bs-toggle="popover" data-bs-content=\''+ alt_portrait +'\' >';
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
                        'data-ajax_url="/ledger/api/corporation/'+ corporationPk +'/character/'+ row.main_id + '/ledger/template/year/' + selectedYear + '/month/0/" ' +
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
                    targets: [3],
                    className: 'text-end',
                },
            ],
            footerCallback: function (row, data, start, end, display) {
                var totalAmountAllChars = parseFloat(total_amount);
                var totalEssAmountAllChars = parseFloat(total_amount_ess);
                var totalCombinedAmountAllChars = parseFloat(total_amount_combined);
                $('#foot-Year .col-total-amount').html('' + formatAndColor(totalAmountAllChars) + '');
                $('#foot-Year .col-total-ess').html('' + formatAndColor(totalEssAmountAllChars) + '');
                $('#foot-Year .col-total-gesamt').html('' + formatAndColor(totalCombinedAmountAllChars) + '');
                $('#foot-Year .col-total-button').html('<button class="btn btn-sm btn-info btn-square" data-bs-toggle="modal" data-bs-target="#modalViewCharacterContainer"' +
                'aria-label="{{ data.main_name }}"' +
                'data-ajax_url="/ledger/api/corporation/'+ corporationPk +'/character/' + corporationPk + '/ledger/template/year/' + selectedYear + '/month/0/?corp=true" ' +
                'title="{{ data.main_name }}"> <span class="fas fa-info"></span></button>')
                    .addClass('text-end');
            },
            initComplete: function(settings, json) {
                $('#foot-Year').show();
                // Initialize popover
                var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
                var popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
                // eslint-disable-next-line no-undef
                    return new bootstrap.Popover(popoverTriggerEl, {
                        html: true
                    });
                });
            }
        });
    },
    error: function(xhr, status, error) {
        if (xhr.status === 403) {
            hideLoading('Year');
            $('#ratting-Year').hide();
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

    if (!data) {
        return;
    }

    // Billboard
    if (data.charts) {
        $('#ChartContainer-' + id).removeClass('d-none');
        var maxpg = 0;
        data.charts.forEach(function (arr) {
            if (maxpg < arr[0]) {
                maxpg = arr[0];
            }
        });
        // Store the chart in the charts object using id as the key
        window.charts['chart' + id] = bb.generate({
            data: {
                columns: data.charts,
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
    if (data.rattingbar) {
        $('#rattingBarContainer-' + id).removeClass('d-none');

        var columnCount = 0;
        let baseRatio = 1.0; // Basiswert für den ratio
        let decreaseFactor = 0.1; // Gewünschter Abnahmefaktor

        // Count 'x' arrays
        var xArray = data.rattingbar.find(function(arr) {
            return arr[0] === 'x';
        });

        if (xArray) {
            // Subtract 'x' array from the total count
            columnCount = xArray.length - 1;
        }

        // ---- Stacks Bar Optional ----
        var groups = data.rattingbar.filter(function(arr) {
            return arr[0] !== 'x';
        }).map(function(arr) {
            return arr[0]; // Nur die Bezeichnungen extrahieren
        });

        window.bar['bar' + id] = bb.generate({
            data: {
                x: 'x',
                columns: data.rattingbar,
                type: 'bar',
                groups: [groups],
            },
            axis: {
                x: {
                    padding: { mode: 'fit' },
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
            bar: {
                width: {
                    ratio: baseRatio / (1 + decreaseFactor * columnCount),
                    max: 25,
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
    setBillboardData(BillboardUrl, 'Month');
    setBillboardData(BillboardUrlYear, 'Year');

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
    }, 100);
    setTimeout(function() {
        // Überprüfen, ob das spezifische Tab aktiv ist
        if ($('#currentMonthLink').hasClass('active')) {
            loadBillboard(BillboardMonth, 'Month');
        }
    }, 100);
});
