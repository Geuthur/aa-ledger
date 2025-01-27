/* global ledgersettings */
/* global bb, d3 */

var MonthUrl, YearUrl, BillboardUrl, BillboardUrlYear;
var BillboardMonth, BillboardYear, BillboardHourly;
var ActiveBillboardMonth, selectedMode;

const entityPk = ledgersettings.entity_pk;
const entityType = ledgersettings.entity_type;
const characteraltsShow = ledgersettings.altShow;
const overviewText = ledgersettings.overviewText;
const planetaryText = ledgersettings.planetaryText;
const hourlyText = ledgersettings.hourlyText;
const daysText = ledgersettings.daysText;

// Aktuelles Datumobjekt erstellen
const currentDate = new Date();

// Aktuelles Jahr und Monat abrufen
var selectedYear = currentDate.getFullYear();
var selectedMonth = currentDate.getMonth() + 1;
var monthText = getMonthName(selectedMonth);

var mainAlts = '';
// Check if altShow is true and append '?main=True' to the URLs
if (characteraltsShow) {
    mainAlts = '?main=True';
}

function updateUrls() {
    MonthUrl = '/ledger/api/'+ entityType +'/' + entityPk + '/ledger/year/' + selectedYear + '/month/' + selectedMonth + '/' + mainAlts;
    YearUrl = '/ledger/api/'+ entityType +'/' + entityPk + '/ledger/year/' + selectedYear + '/month/0/' + mainAlts;
    BillboardUrl = '/ledger/api/'+ entityType +'/' + entityPk + '/billboard/year/' + selectedYear + '/month/' + selectedMonth + '/' + mainAlts;
    BillboardUrlYear = '/ledger/api/'+ entityType +'/' + entityPk + '/billboard/year/' + selectedYear + '/month/0/' + mainAlts;
}

function getMonthName(monthNumber) {
    const months = ['January', 'February', 'March', 'April', 'May', 'June',
        'July', 'August', 'September', 'October', 'November', 'December'];
    return months[monthNumber - 1]; // Array ist 0-basiert, daher -1
}

// Function to format currency and apply color
function formatAndColor(value) {
    // Ensure data is a number
    let number = parseFloat(value) || 0;

    // Round the number to the nearest integer
    number = Math.round(number);

    // Format the number to two decimal places
    const formattedNumber = number.toLocaleString();

    // Determine the CSS class based on the value
    const cssClass = number < 0 ? 'text-danger' : (number > 0 ? 'text-success' : '');

    // Return the formatted number wrapped in a span with the appropriate class
    return `<span class="${cssClass}">${formattedNumber}</span> ISK`;
}

$('#monthDropdown li').click(function() {
    showLoading('Month');
    hideContainer('Month');

    if (entityPk === 0 || (entityPk > 0 && characteraltsShow && entityType !== 'character')) {
        window['MonthTable'].clear().draw();
        $('#foot-Month').hide();
    }

    selectedMonth = $(this).find('a').data('bs-month-id');
    monthText = getMonthName(selectedMonth);

    // Update URL Data
    updateUrls();

    // DataTable neu laden mit den Daten des ausgewählten Monats
    setBillboardData(BillboardUrl, 'Month');
    generateLedger('Month', MonthUrl);
    $('#currentMonthLink').text('Month - ' + monthText);
});

$('#yearDropdown li').click(function() {
    showLoading('Year');
    showLoading('Month');
    hideContainer('Year');
    hideContainer('Month');

    if (entityPk === 0 || (entityPk > 0 && characteraltsShow && entityType !== 'character')) {
        window['YearTable'].clear().draw();
        $('#foot-Year').hide();
        window['MonthTable'].clear().draw();
        $('#foot-Month').hide();
    }

    selectedYear = $(this).text();

    // Update URL Data
    updateUrls();

    // DataTable neu laden mit den Daten des ausgewählten Monats
    setBillboardData(BillboardUrl, 'Month');
    setBillboardData(BillboardUrlYear, 'Year');
    generateLedger('Month', MonthUrl);
    generateLedger('Year', YearUrl);
    $('#currentMonthLink').text('Month - ' + monthText);
    $('#currentYearLink').text('Year - ' + selectedYear);
});

$('#barDropdown-Month li').click(function() {
    selectedMode = $(this).text();
    if (selectedMode === hourlyText) {
        $('#barTitle-Month').text('Ledger ' + selectedMode);
        ActiveBillboardMonth = BillboardHourly;
    } else {
        $('#barTitle-Month').text('Ledger 30 '+ daysText +'');
        ActiveBillboardMonth = BillboardMonth;
    }
    updateBillboard(ActiveBillboardMonth, 'Month', selectedMode);
});

function initTooltip() {
    $('[data-tooltip-toggle="ledger-tooltip"]').tooltip({
        trigger: 'hover',
    });
    if (entityType !== 'character') {
        $('[data-bs-toggle="corp-popover"]').popover({
            trigger: 'hover',
            html: true,
        });
    }
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
    $('#lookup-'+id).addClass('d-none');
    $('#ChartContainer-'+id).addClass('d-none');
    $('#rattingBarContainer-'+id).addClass('d-none');
    $('#workGaugeContainer-'+id).addClass('d-none');
}

function setBillboardData(url, id) {
    $.ajax({
        url: url,
        type: 'GET',
        success: function(data) {
            if (id === 'Month') {
                BillboardMonth = data[0].billboard.standard;
                if (entityType === 'character') {
                    BillboardHourly = data[0].billboard.hourly;
                    ActiveBillboardMonth = BillboardMonth;
                }
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
            hideLoading(''+ TableName +'');
            const char_name = data[0].ratting[0]?.main_name || 'No Data';
            const char_id = data[0].ratting[0]?.main_id || '0';
            const total_amount = data[0].total.total_amount;
            const total_amount_ess = data[0].total.total_amount_ess;
            const total_amount_others = data[0].total.total_amount_others;
            const total_amount_mining = data[0].total.total_amount_mining;
            const total_amount_combined = data[0].total.total_amount_all;
            const total_amount_costs = data[0].total.total_amount_costs;

            // Set the month to 0 for the year table
            const tableMonth = (TableName === 'Year') ? 0 : selectedMonth;

            if (entityPk > 0 && !characteraltsShow && entityType === 'character') {
                $('#lookup-'+ TableName +'').removeClass('d-none');
                // Daten direkt in die HTML-Elemente einfügen
                $('#portrait-'+ TableName +'').html('<img width="256" height="256" class="rounded" src="https://images.evetech.net/characters/' + char_id + '/portrait?size=256">');
                $('#character_name-'+ TableName +'').text(char_name);
                $('#amount_ratting-'+ TableName +'').html(formatAndColor(total_amount));
                $('#amount_ess-'+ TableName +'').html(formatAndColor(total_amount_ess));
                $('#amount_mining-'+ TableName +'').html(formatAndColor(total_amount_mining));
                $('#amount_misc-'+ TableName +'').html(formatAndColor(total_amount_others));
                $('#amount_costs-'+ TableName +'').html(formatAndColor(total_amount_costs));
                $('#amount_summary-'+ TableName +'').html(formatAndColor(total_amount_combined));
                $('#planetary_interaction-'+ TableName +'').html(`
                    <a href="/ledger/planetary_ledger/${entityPk}/">
                        <image src="/static/ledger/images/pi.png"
                            title="${planetaryText}"
                            height="256" data-tooltip-toggle="ledger-tooltip" data-bs-placement="top">
                    </a>
                `);
                $('#get_template-'+ TableName +'').html(`
                    <button
                        class="btn btn-sm btn-info btn-square" id="button-${TableName}"
                        data-bs-toggle="modal"
                        data-bs-target="#modalViewCharacterContainer"
                        aria-label="${char_name}"
                        data-ajax_url="/ledger/api/${entityType}/${char_id}/template/year/${selectedYear}/month/${tableMonth}/"
                        title="${char_name}"
                        data-tooltip-toggle="ledger-tooltip" data-bs-placement="right">
                        <span class="fas fa-info"></span>
                    </button>
                `);
                const infobutton = document.getElementById('button-'+ TableName +'');
                if (!data[0].ratting[0]?.main_name) {
                    infobutton.classList.add('disabled');
                }
                initTooltip();
            } else {
                var table = TableName + 'Table';
                window[table] = $('#ratting-'+ TableName +'').DataTable({
                    data: data[0].ratting,
                    columns: [
                        {
                            data: 'main_name',
                            render: function (data, _, row) {
                                var imageUrl = 'https://images.evetech.net/';
                                if (row.entity_type === 'character' && row.main_id) {
                                    imageUrl += 'characters/' + row.main_id + '/portrait?size=32';
                                } else if (row.entity_type === 'corporation' && row.main_id) {
                                    imageUrl += 'corporations/' + row.main_id + '/logo?size=32';
                                } else if (row.entity_type === 'alliance' && row.main_id) {
                                    imageUrl += 'alliances/' + row.main_id + '/logo?size=32';
                                } else {
                                    // Fallback image URL if no valid ID is available
                                    imageUrl += 'icons/no-image.png'; // Beispiel für ein Platzhalterbild
                                }

                                var imageHTML = '';

                                if (entityType !== 'character') {
                                    // Initialize alt_names
                                    var alt_portrait = 'Included Characters: ';

                                    // Loop through alt_names and add each image
                                    row.alt_names.forEach(function(character_id) {
                                        alt_portrait += `
                                            <img
                                                src="https://images.evetech.net/characters/${character_id}/portrait?size=32"
                                                class="rounded-circle"
                                            >
                                        `;
                                    });

                                    imageHTML += `
                                        <img
                                            src='${imageUrl}'
                                            class="rounded-circle"
                                            data-bs-toggle="corp-popover"
                                            data-bs-content='${alt_portrait}'> ${data}
                                        `;
                                    return imageHTML;
                                } else {
                                    imageHTML += `
                                        <img src="${imageUrl}"
                                            class="rounded-circle"
                                            title="${data}"
                                            data-tooltip-toggle="ledger-tooltip" data-bs-placement="right"
                                            height="30"> ${data}
                                        `;

                                    if (row.entity_type === 'character') {
                                        imageHTML += `
                                            <a href="/ledger/character_ledger/${row.main_id}/">
                                                <button
                                                    class="btn btn-sm btn-info btn-square"
                                                    id="lookup-Month"
                                                    title="${overviewText}"
                                                    data-tooltip-toggle="ledger-tooltip" data-bs-placement="right">
                                                    <span class="fas fa-search"></span>
                                                </button>
                                            </a>
                                        `;
                                    }
                                    return imageHTML;
                                }
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
                        // Conditionally add columns based on entity_type
                        ...(entityType === 'character' ? [
                            {   data: 'total_amount_mining',
                                render: function (data, type) {
                                    if (type === 'display') {
                                        return formatAndColor(data);
                                    }
                                    return data;
                                }
                            },
                        ] : []),
                        {   data: 'total_amount_others',
                            render: function (data, type) {
                                if (type === 'display') {
                                    return formatAndColor(data);
                                }
                                return data;
                            }
                        },
                        // Conditionally add columns based on entity_type
                        ...(entityType === 'character' ? [
                            {   data: 'total_amount_costs',
                                render: function (data, type) {
                                    if (type === 'display') {
                                        return formatAndColor(data);
                                    }
                                    return data;
                                }
                            }
                        ] : []),
                        {
                            data: 'col-total-action',
                            render: function (_, __, row) {
                                var chartemplateUrl = '';

                                if (entityType === 'character') {
                                    chartemplateUrl = `/ledger/api/character/${row.main_id}/template/year/${selectedYear}/month/${tableMonth}/`;
                                } else {
                                    chartemplateUrl = `/ledger/api/${entityType}/${entityPk}/${row.main_id}/template/year/${selectedYear}/month/${tableMonth}/`;
                                }

                                return `
                                    <button class="btn btn-sm btn-info btn-square"
                                        data-bs-toggle="modal"
                                        data-bs-target="#modalViewCharacterContainer"
                                        data-ajax_url="${chartemplateUrl}"
                                        title="${row.main_name}" data-tooltip-toggle="ledger-tooltip" data-bs-placement="left">
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
                            targets: entityType === 'character' ? [6] : [3],
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

                            if (entityType === 'character') {
                                $('#foot-'+ TableName +' .col-total-mining').html('');
                                $('#foot-'+ TableName +' .col-total-costs').html('');
                            }
                            return;
                        }

                        var templateUrl = '';
                        if (entityType === 'character') {
                            templateUrl = `/ledger/api/character/${entityPk}/template/year/${selectedYear}/month/${tableMonth}/`;
                            if (characteraltsShow) {
                                templateUrl += '?main=True';
                            }
                            $('#foot-'+ TableName +' .col-total-mining').html(formatAndColor(total_amount_mining));
                            $('#foot-'+ TableName +' .col-total-costs').html(formatAndColor(total_amount_costs));
                        } else {
                            templateUrl = `/ledger/api/${entityType}/${entityPk}/0/template/year/${selectedYear}/month/${tableMonth}/?corp=true`;
                        }

                        $('#foot-'+ TableName +' .col-total-amount').html(formatAndColor(total_amount));
                        $('#foot-'+ TableName +' .col-total-ess').html(formatAndColor(total_amount_ess));
                        $('#foot-'+ TableName +' .col-total-others').html(formatAndColor(total_amount_others));
                        $('#foot-'+ TableName +' .col-total-gesamt').html(formatAndColor(total_amount_combined));

                        $('#foot-'+ TableName +' .col-total-button').html(`
                            <button
                                class="btn btn-sm btn-info btn-square"
                                data-bs-toggle="modal"
                                data-bs-target="#modalViewCharacterContainer"
                                data-ajax_url="${templateUrl}">
                                <span class="fas fa-info"></span></button>
                        `).addClass('text-end');
                    },
                    initComplete: function() {
                        $('#foot-'+ TableName +'').show();
                        $('#ratting-'+ TableName +'').removeClass('d-none');
                        initTooltip();
                    },
                    drawCallback: function() {
                        initTooltip();
                    }
                });
            }
        },
        error: function(xhr, _, __) {
            if (xhr.status === 403) {
                $('#ratting-'+ TableName +'').DataTable().destroy();
                hideLoading(''+ TableName +'');
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
    // Initialize the URLs
    updateUrls();

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
            if (entityType === 'character') {
                updateBillboard(ActiveBillboardMonth, 'Month', selectedMode);
            }
        }
    }, 100);
});
