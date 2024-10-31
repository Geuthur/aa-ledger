/* global corporationsettings */
/* global bb, d3 */
var MonthUrl, YearUrl, BillboardUrl, BillboardUrlYear;
var BillboardMonth, BillboardYear;

const corporationPk = corporationsettings.corporation_pk;

// Aktuelles Datumobjekt erstellen
const currentDate = new Date();

// Aktuelles Jahr und Monat abrufen
var selectedYear = currentDate.getFullYear();
var selectedMonth = currentDate.getMonth() + 1;
var monthText = getMonthName(selectedMonth);

function updateUrls() {
    MonthUrl = '/ledger/api/corporation/' + corporationPk + '/ledger/year/' + selectedYear + '/month/' + selectedMonth + '/';
    YearUrl = '/ledger/api/corporation/' + corporationPk + '/ledger/year/' + selectedYear + '/month/0/';
    BillboardUrl = '/ledger/api/corporation/' + corporationPk + '/billboard/year/' + selectedYear + '/month/' + selectedMonth + '/';
    BillboardUrlYear = '/ledger/api/corporation/' + corporationPk + '/billboard/year/' + selectedYear + '/month/0/';
}

function getMonthName(monthNumber) {
    const months = ['January', 'February', 'March', 'April', 'May', 'June',
        'July', 'August', 'September', 'October', 'November', 'December'];
    return months[monthNumber - 1]; // Array ist 0-basiert, daher -1
}

// Function to format currency and apply color
function formatAndColor(value) {
    // Ensure data is a number
    const number = parseInt(value) || 0;

    // Format the number to two decimal places
    const formattedNumber = number.toLocaleString();

    // Determine the CSS class based on the value
    const cssClass = number < 0 ? 'text-danger' : 'text-success';

    // Return the formatted number wrapped in a span with the appropriate class
    return `<span class="${cssClass}">${formattedNumber}</span> ISK`;
}

$('#monthDropdown li').click(function() {
    showLoading('Month');
    hideContainer('Month');

    window['MonthTable'].clear().draw();
    $('#foot-Month').hide();

    selectedMonth = $(this).find('a').data('bs-month-id');
    monthText = getMonthName(selectedMonth);

    // Update URLs
    updateUrls();

    // Daten neu laden mit den Daten des ausgewählten Monats
    setBillboardData(BillboardUrl, 'Month');
    generateLedger('Month', MonthUrl);
    $('#currentMonthLink').text('Month - ' + monthText);
});

$('#yearDropdown li').click(function() {
    showLoading('Year');
    showLoading('Month');
    hideContainer('Year');
    hideContainer('Month');

    window['YearTable'].clear().draw();
    $('#foot-Year').hide();

    window['MonthTable'].clear().draw();
    $('#foot-Month').hide();

    selectedYear = $(this).text();

    // Update URLs
    updateUrls();

    // Daten neu laden mit den Daten des ausgewählten Jahres
    setBillboardData(BillboardUrl, 'Month');
    setBillboardData(BillboardUrlYear, 'Year');
    generateLedger('Month', MonthUrl);
    generateLedger('Year', YearUrl);
    $('#currentMonthLink').text('Month - ' + monthText);
    $('#currentYearLink').text('Year - ' + selectedYear);
});

function initializeTooltipsAndPopovers() {
    $('[data-tooltip-toggle="corp-tooltip"]').tooltip({
        trigger: 'hover',
    });
    $('[data-bs-toggle="corp-popover"]').popover({
        trigger: 'hover',
        html: true,
    });
}

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

function generateLedger(TableName, url) {
    return $.ajax({
        url: url,
        type: 'GET',
        success: function(data) {
            if (window[TableName + 'Table']) {
                $('#ratting-'+ TableName +'').DataTable().destroy();
            }
            hideLoading(TableName);
            const total_amount = data[0].total.total_amount;
            const total_amount_ess = data[0].total.total_amount_ess;
            const total_amount_other = data[0].total.total_amount_others;
            const total_amount_combined = data[0].total.total_amount_all;

            // Set the month to 0 for the year table
            var tableMonth = (TableName === 'Year') ? 0 : selectedMonth;

            // DataTable neu initialisieren
            var table = TableName + 'Table';
            window[table] = $('#ratting-'+ TableName +'').DataTable({
                data: data[0].ratting,
                columns: [
                    {
                        data: 'main_name',
                        render: function (data, _, row) {
                            // Initialize alt_names
                            var alt_portrait = 'Included Characters: ';

                            // Loop through alt_names and add each image
                            row.alt_names.forEach(function(character_id) {
                                alt_portrait += `
                                    <img
                                        src="https://images.evetech.net/characters/${character_id}/portrait?size=32"
                                        class="rounded-circle"
                                        height="30"
                                    >
                                `;
                            });

                            var imageHTML = `
                                <img
                                    src="https://images.evetech.net/characters/${row.main_id}/portrait?size=32"
                                    class="rounded-circle"
                                    height="30"
                                    data-bs-toggle="corp-popover"
                                    data-bs-content='${alt_portrait}'> ${data}
                                `;
                            return imageHTML;
                        }
                    },
                    {   data: 'total_amount',
                        render: function (data, type) {
                            if (type === 'display') {
                                return formatAndColor(data);
                            }
                            return data;
                        }
                    },
                    {   data: 'total_amount_ess',
                        render: function (data, type) {
                            if (type === 'display') {
                                return formatAndColor(data);
                            }
                            return data;
                        }
                    },
                    {   data: 'total_amount_others',
                        render: function (data, type) {
                            if (type === 'display') {
                                return formatAndColor(data);
                            }
                            return data;
                        }
                    },
                    {
                        data: 'col-total-action',
                        render: function (_, __, row) {
                            return `
                                <button class="btn btn-sm btn-info btn-square"
                                    data-bs-toggle="modal"
                                    data-bs-target="#modalViewCharacterContainer"
                                    data-ajax_url="/ledger/api/corporation/${corporationPk}/character/${row.main_id}/ledger/template/year/${selectedYear}/month/${tableMonth}/"
                                    title="${row.main_name}" data-tooltip-toggle="corp-tooltip" data-bs-placement="left">
                                    <span class="fas fa-info"></span>
                                </button>
                            `;
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
                footerCallback: function (_, data, __, ___, ____) {
                    if (data.length === 0) {
                        $('#foot-'+ TableName +' .col-total-amount').html('');
                        $('#foot-'+ TableName +' .col-total-ess').html('');
                        $('#foot-'+ TableName +' .col-total-others').html('');
                        $('#foot-'+ TableName +' .col-total-gesamt').html('');
                        $('#foot-'+ TableName +' .col-total-button').html('').removeClass('text-end');
                        return;
                    }
                    $('#foot-'+ TableName +' .col-total-amount').html(formatAndColor(total_amount));
                    $('#foot-'+ TableName +' .col-total-ess').html(formatAndColor(total_amount_ess));
                    $('#foot-'+ TableName +' .col-total-others').html(formatAndColor(total_amount_other));
                    $('#foot-'+ TableName +' .col-total-gesamt').html(formatAndColor(total_amount_combined));
                    $('#foot-'+ TableName +' .col-total-button').html(`
                        <button
                            class="btn btn-sm btn-info btn-square"
                            data-bs-toggle="modal"
                            data-bs-target="#modalViewCharacterContainer"
                            data-ajax_url="/ledger/api/corporation/${corporationPk}/character/${corporationPk}/ledger/template/year/${selectedYear}/month/${tableMonth}/?corp=true">
                            <span class="fas fa-info"></span></button>
                        `).addClass('text-end');
                },
                initComplete: function() {
                    $('#foot-'+ TableName +'').show();
                    $('#ratting-'+ TableName +'').removeClass('d-none');
                    initializeTooltipsAndPopovers();
                },
                drawCallback: function() {
                    initializeTooltipsAndPopovers();
                }
            });
        },
        error: function(xhr, _, __) {
            if (xhr.status === 403) {
                hideLoading(''+ TableName +'');
                $('#ratting-'+ TableName +'').hide();
                $('#errorHandler-'+ TableName +'').removeClass('d-none');
                $('.dropdown-toggle').attr('disabled', true);
                $('.overview').attr('disabled', true);
            }
        }
    });
}

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
    // Update URLs
    updateUrls();

    // Initialize Billboard
    setBillboardData(BillboardUrl, 'Month');
    setBillboardData(BillboardUrlYear, 'Year');

    // Initialize DataTable
    generateLedger('Month', MonthUrl);
    generateLedger('Year', YearUrl);
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
