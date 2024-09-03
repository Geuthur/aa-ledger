/* global charactersettings */

var MonthTable, YearTable;
var bb, d3;
var BillboardMonth, BillboardYear, BillboardHourly;
var ActiveBillboardMonth, selectedMode;

var characterPk = charactersettings.character_pk;
var characteraltsShow = charactersettings.altShow;

// Aktuelles Datumobjekt erstellen
var currentDate = new Date();

// Aktuelles Jahr und Monat abrufen
var selectedYear = currentDate.getFullYear();
var selectedMonth = currentDate.getMonth() + 1;
var monthText = getMonthName(selectedMonth);

var mainAlts = '';
// Check if altShow is true and append '?main=True' to the URLs
if (characteraltsShow) {
    mainAlts = '?main=True';
}

// Billboard URLs
var MonthUrl = '/ledger/api/account/' + characterPk + '/ledger/year/' + selectedYear + '/month/' + selectedMonth + '/' + mainAlts;
var YearUrl = '/ledger/api/account/' + characterPk + '/ledger/year/' + selectedYear + '/month/0/' + mainAlts;
var BillboardUrl = '/ledger/api/account/' + characterPk + '/billboard/year/' + selectedYear + '/month/' + selectedMonth + '/' + mainAlts;
var BillboardUrlYear = '/ledger/api/account/' + characterPk + '/billboard/year/' + selectedYear + '/month/0/' + mainAlts;

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
    var color = value > 0 ? 'chartreuse' : (value < 0 ? 'red' : 'white');

    // Rückgabe des formatierten Strings mit Farbe und Einheit
    return '<span style="color: ' + color + ';">' + formattedValue + '</span> ISK';
}

$('#monthDropdown li').click(function() {
    showLoading('Month');
    hideContainer('Month');

    if (characterPk === 0 || (characterPk > 0 && characteraltsShow)) {
        MonthTable.clear().draw();
        $('#foot-Month').hide();
    }

    selectedMonth = $(this).find('a').data('bs-month-id');
    monthText = getMonthName(selectedMonth);

    // URL für die Daten der ausgewählten Kombination von Jahr und Monat erstellen
    var newurl = '/ledger/api/account/' + characterPk + '/ledger/year/' + selectedYear + '/month/' + selectedMonth + '/' + mainAlts;
    var BillboardUrl = '/ledger/api/account/' + characterPk + '/billboard/year/' + selectedYear + '/month/' + selectedMonth + '/' + mainAlts;

    // DataTable neu laden mit den Daten des ausgewählten Monats
    setBillboardData(BillboardUrl, 'Month');
    reloadAjax(newurl, MonthAjax);
    $('#currentMonthLink').text('Month - ' + monthText);
});

$('#yearDropdown li').click(function() {
    showLoading('Year');
    showLoading('Month');
    hideContainer('Year');
    hideContainer('Month');
    if (characterPk === 0 || (characterPk > 0 && characteraltsShow)) {
        YearTable.clear().draw();
        $('#foot-Year').hide();
        MonthTable.clear().draw();
        $('#foot-Month').hide();
    }

    selectedYear = $(this).text();

    // URL für die Daten der ausgewählten Kombination von Jahr und Monat erstellen
    var newurl = '/ledger/api/account/' + characterPk + '/ledger/year/' + selectedYear + '/month/' + selectedMonth + '/' + mainAlts;
    var newurl_year = '/ledger/api/account/' + characterPk + '/ledger/year/' + selectedYear + '/month/0/' + mainAlts;
    var BillboardUrl = '/ledger/api/account/' + characterPk + '/billboard/year/' + selectedYear + '/month/' + selectedMonth + '/' + mainAlts;
    var BillboardUrlYear = '/ledger/api/account/' + characterPk + '/billboard/year/' + selectedYear + '/month/0/' + mainAlts;

    // DataTable neu laden mit den Daten des ausgewählten Monats
    setBillboardData(BillboardUrl, 'Month');
    setBillboardData(BillboardUrlYear, 'Year');
    reloadAjax(newurl, MonthAjax);
    reloadAjax(newurl_year, YearAjax);
    $('#currentMonthLink').text('Month - ' + monthText);
    $('#currentYearLink').text('Year - ' + selectedYear);
});

$('#barDropdown-Month li').click(function() {
    selectedMode = $(this).text();
    if (selectedMode === 'Hourly') {
        $('#barTitle-Month').text('Ledger ' + selectedMode);
        ActiveBillboardMonth = BillboardHourly;
    } else {
        $('#barTitle-Month').text('Ledger 30 Days');
        ActiveBillboardMonth = BillboardMonth;
    }
    updateBillboard(ActiveBillboardMonth, 'Month', selectedMode);
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
    $('#lookup-'+id).addClass('d-none');
    $('#ChartContainer-'+id).addClass('d-none');
    $('#rattingBarContainer-'+id).addClass('d-none');
    $('#workGaugeContainer-'+id).addClass('d-none');
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
                BillboardHourly = data[0].billboard.hourly;
                ActiveBillboardMonth = BillboardMonth;
                loadBillboard(data[0].billboard.standard, 'Month');
            } else {
                BillboardYear = data[0].billboard.standard;
                loadBillboard(data[0].billboard.standard, 'Year');
            }
        }
    });
}

var MonthAjax = {
    url: MonthUrl,
    type: 'GET',
    success: function(data) {
        if (MonthTable) {
            $('#ratting-Month').DataTable().destroy();
        }
        hideLoading('Month');
        var char_name = data[0].ratting[0]?.main_name || 'No Data';
        var char_id = data[0].ratting[0]?.main_id || '0';
        var total_amount = data[0].total.total_amount;
        var total_amount_ess = data[0].total.total_amount_ess;
        var total_amount_others = data[0].total.total_amount_others;
        var total_amount_mining = data[0].total.total_amount_mining;
        var total_amount_combined = data[0].total.total_amount_all;
        var total_amount_costs = data[0].total.total_amount_costs;

        if (characterPk > 0 && !characteraltsShow) {
            $('#lookup-Month').removeClass('d-none');
            // Daten direkt in die HTML-Elemente einfügen
            $('#portrait-Month').html('<img width="256" height="256" class="rounded" src="https://images.evetech.net/characters/' + char_id + '/portrait?size=256">');
            $('#character_name-Month').text(char_name);
            $('#amount_ratting-Month').html('' + formatAndColor(total_amount) + '');
            $('#amount_ess-Month').html('' + formatAndColor(total_amount_ess) + '');
            $('#amount_mining-Month').html('' + formatAndColor(total_amount_mining) + '');
            $('#amount_misc-Month').html('' + formatAndColor(total_amount_others) + '');
            $('#amount_costs-Month').html('' + formatAndColor(total_amount_costs) + '');
            $('#amount_summary-Month').html('' + formatAndColor(total_amount_combined) + '');
            $('#get_template-Month').html('<button class="btn btn-sm btn-info btn-square" id="button-Month" ' +
                            'data-bs-toggle="modal" ' +
                            'data-bs-target="#modalViewCharacterContainer" ' +
                            'aria-label="' + char_name + '" ' +
                            'data-ajax_url="/ledger/api/account/'+ char_id + '/ledger/template/year/' + selectedYear + '/month/' + selectedMonth + '/" ' +
                            'title="' + char_name + '">' +
                            '<span class="fas fa-search"></span>' +
                            '</button>'
            );
            var infobutton = document.getElementById('button-Month');
            if (!data[0].ratting[0]?.main_name) {
                infobutton.classList.add('disabled');
            }
        } else {
            MonthTable = $('#ratting-Month').DataTable({
                data: data[0].ratting,
                columns: [
                    {
                        data: 'main_name',
                        render: function (data, type, row) {
                            var imageHTML = '<img src="https://images.evetech.net/characters/' + row.main_id + '/portrait?size=32" class="rounded-circle" title="' + data + '" height="30">';
                            return imageHTML + ' ' + data + ' <a href="/ledger/character_ledger/' + row.main_id + '/"><button class="btn btn-sm btn-info btn-square" id="lookup-Month" ' +
                            'title="' + row.main_name + ' Single Lookup">' +
                            '<span class="fas fa-search"></span>' +
                            '</button></a>';
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
                    {   data: 'total_amount_costs',
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
                        targets: [6],
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

                    $('#foot-Month .col-total-amount').html('' + formatAndColor(totalAmountAllChars) + '');
                    $('#foot-Month .col-total-ess').html('' + formatAndColor(totalEssAmountAllChars) + '');
                    $('#foot-Month .col-total-mining').html('' + formatAndColor(totalMiningAmountAllChars) + '');
                    $('#foot-Month .col-total-others').html('' + formatAndColor(totalOthersAmountAllChars) + '');
                    $('#foot-Month .col-total-gesamt').html('' + formatAndColor(totalCombinedAmountAllChars) + '');
                    $('#foot-Month .col-total-costs').html('' + formatAndColor(totalCostsAmountAllChars) + '');
                    $('#foot-Month .col-total-button').html('<button class="btn btn-sm btn-info btn-square" data-bs-toggle="modal" data-bs-target="#modalViewCharacterContainer"' +
                        'aria-label="{{ data.main_name }}"' +
                        'data-ajax_url="/ledger/api/account/' + characterPk + '/ledger/template/year/' + selectedYear + '/month/' + selectedMonth + '/" ' +
                        'title="{{ data.main_name }}"> <span class="fas fa-info"></span></button>')
                        .addClass('text-end');
                },
                initComplete: function(settings, json) {
                    $('#foot-Month').show();
                    $('#ratting-Month').removeClass('d-none');
                }
            });
        }
    },
    error: function(xhr, status, error) {
        if (xhr.status === 403) {
            hideLoading('Month');
            if (MonthTable) {
                $('#ratting-Month').hide();
            }
            $('#errorHandler').removeClass('d-none');
            $('.dropdown-toggle').attr('disabled', true);
        }
    }
};

var YearAjax = {
    url: YearUrl,
    type: 'GET',
    success: function(data) {
        if (YearTable) {
            $('#ratting-Year').DataTable().destroy();
        }
        hideLoading('Year');
        // Zusätzliche Daten im DataTable-Objekt speichern
        var char_name = data[0].ratting[0]?.main_name || 'No Data';
        var char_id = data[0].ratting[0]?.main_id || '';
        var total_amount = data[0].total.total_amount;
        var total_amount_ess = data[0].total.total_amount_ess;
        var total_amount_mining = data[0].total.total_amount_mining;
        var total_amount_others = data[0].total.total_amount_others;
        var total_amount_combined = data[0].total.total_amount_all;
        var total_amount_costs = data[0].total.total_amount_costs;

        if (characterPk > 0 && !characteraltsShow) {
            $('#lookup-Year').removeClass('d-none');
            // Daten direkt in die HTML-Elemente einfügen
            $('#portrait-Year').html('<img width="256" height="256" class="rounded" src="https://images.evetech.net/characters/' + char_id + '/portrait?size=256">');
            $('#character_name-Year').text(char_name);
            $('#amount_ratting-Year').html('' + formatAndColor(total_amount) + '');
            $('#amount_ess-Year').html('' + formatAndColor(total_amount_ess) + '');
            $('#amount_mining-Year').html('' + formatAndColor(total_amount_mining) + '');
            $('#amount_misc-Year').html('' + formatAndColor(total_amount_others) + '');
            $('#amount_costs-Year').html('' + formatAndColor(total_amount_costs) + '');
            $('#amount_summary-Year').html('' + formatAndColor(total_amount_combined) + '');
            $('#get_template-Year').html('<button class="btn btn-sm btn-info btn-square" id="button-Year" ' +
                            'data-bs-toggle="modal" ' +
                            'data-bs-target="#modalViewCharacterContainer" ' +
                            'aria-label="' + char_name + '" ' +
                            'data-ajax_url="/ledger/api/account/'+ char_id + '/ledger/template/year/' + selectedYear + '/month/0/" ' +
                            'title="' + char_name + '">' +
                            '<span class="fas fa-search"></span>' +
                            '</button>'
            );
            var infobutton = document.getElementById('button-Year');
            if (!data[0].ratting[0]?.main_name) {
                infobutton.classList.add('disabled');
            }

            $('#foot-Year').show();
        } else {
            YearTable = $('#ratting-Year').DataTable({
                data: data[0].ratting,
                columns: [
                    {
                        data: 'main_name',
                        render: function (data, type, row) {
                            var imageHTML = '<img src="https://images.evetech.net/characters/' + row.main_id + '/portrait?size=32" class="rounded-circle" title="' + data + '" height="30">';
                            return imageHTML + ' ' + data + ' <a href="/ledger/character_ledger/' + row.main_id + '/"><button class="btn btn-sm btn-info btn-square" id="lookup-Year" ' +
                            'title="' + row.main_name + ' Single Lookup">' +
                            '<span class="fas fa-search"></span>' +
                            '</button></a>';
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
                    {   data: 'total_amount_costs',
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
                        targets: [6],
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

                    $('#foot-Year .col-total-amount').html('' + formatAndColor(totalAmountAllChars_year) + '');
                    $('#foot-Year .col-total-ess').html('' + formatAndColor(totalEssAmountAllChars_year) + '');
                    $('#foot-Year .col-total-mining').html('' + formatAndColor(totalMiningAmountAllChars_year) + '');
                    $('#foot-Year .col-total-others').html('' + formatAndColor(totalOthersAmountAllChars_year) + '');
                    $('#foot-Year .col-total-gesamt').html('' + formatAndColor(totalCombinedAmountAllChars_year) + '');
                    $('#foot-Year .col-total-costs').html('' + formatAndColor(totalCostsAmountAllChars_year) + '');
                    $('#foot-Year .col-total-button').html('<button class="btn btn-sm btn-info btn-square" data-bs-toggle="modal" data-bs-target="#modalViewCharacterContainer"' +
                    'data-ajax_url="/ledger/api/account/' + char_id + '/ledger/template/year/' + selectedYear + '/month/0/" ' +
                    '"> <span class="fas fa-info"></span></button>')
                        .addClass('text-end');
                },
                initComplete: function(settings, json) {
                    $('#foot-Year').show();
                    $('#ratting-Year').removeClass('d-none');
                }
            });
        }
    },
    error: function(xhr, status, error) {
        if (xhr.status === 403) {
            hideLoading('Year');
            if (YearTable) {
                $('#ratting-Year').hide();
            }
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
                show: false
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
        var columnCount = 0;
        let baseRatio = 1.0; // Basiswert für den ratio
        let decreaseFactor = 0.2; // Gewünschter Abnahmefaktor

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
                    type: 'timeseries',
                    tick: {
                        format: '%Y-%m' + (id === 'Month' ? '-%d' : ''),
                        rotate: 45,
                    },
                    padding: { mode: 'fit' },
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
                    max: 25
                }
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
        var columnCount = 0;
        let baseRatio = 1.0; // Basiswert für den ratio
        let decreaseFactor = 0.2 * (selectedMode === 'Hourly' ? 0.1:1); // Gewünschter Abnahmefaktor

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
            return arr[0] !== 'x' && arr[0] !== 'Tick';
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
                    type: 'timeseries',
                    tick: {
                        format: '%Y-%m' + (id === 'Month' ? '-%d' : '') + (selectedMode === 'Hourly' ? ' %H:00:00' : ''),
                        rotate: 45,
                    },
                    padding: { mode: 'fit' },
                },
                y: {
                    tick: { format: function(x) { return d3.format(',')(x); } },
                    label: 'ISK',
                },
            },
            bar: {
                width: {
                    ratio: baseRatio / (1 + decreaseFactor * columnCount),
                    max: 25
                },
            },
            padding: true,
            bindto: '#rattingBar-'+id,
            legend: {
                show: true
            }
        });
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
            updateBillboard(ActiveBillboardMonth, 'Month', selectedMode);
        }
    }, 100);
});
