/* global ledgersettings, load_or_create_Chart, setBillboardData */
/* eslint-disable */

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
var selectedDay = 1;
var monthText = getMonthName(selectedMonth);

var mainAlts = '';
// Check if altShow is true and append '?main=True' to the URLs
if (characteraltsShow) {
    mainAlts = '?main=True';
}

function updateUrls() {
    MonthUrl = `/ledger/api/${entityType}/${entityPk}/ledger/date/${selectedYear}-${selectedMonth}-${selectedDay}/view/month/${mainAlts}`;
    YearUrl = `/ledger/api/${entityType}/${entityPk}/ledger/date/${selectedYear}-${selectedMonth}-${selectedDay}/view/year/${mainAlts}`;
    BillboardUrl = `/ledger/api/${entityType}/${entityPk}/billboard/date/${selectedYear}-${selectedMonth}-${selectedDay}/view/month/${mainAlts}`;
    BillboardUrlYear = `/ledger/api/${entityType}/${entityPk}/billboard/date/${selectedYear}-${selectedMonth}-${selectedDay}/view/year/${mainAlts}`;
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
    var div = 'rattingBar-Month';
    if (selectedMode === hourlyText) {
        var data = BillboardHourly.rattingbar;
    } else {
        var data = BillboardMonth.rattingbar;
    }
    const success = load_or_create_Chart(div=div, data=data, id='Month', chart='bar');
    if (success) {
        $('#barTitle-Month').text('Ledger ' + selectedMode);
        console.log('Chart loaded successfully');
    } else {
        console.error('Failed to load chart');
    }
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
            const tableView = TableName.toLowerCase();

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
                        data-ajax_url="/ledger/api/${entityType}/${char_id}/template/date/${selectedYear}-${selectedMonth}-${selectedDay}/view/${tableView}/"
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
                                    chartemplateUrl = `/ledger/api/character/${row.main_id}/template/date/${selectedYear}-${selectedMonth}-${selectedDay}/view/${tableView}/`;
                                } else {
                                    chartemplateUrl = `/ledger/api/${entityType}/${entityPk}/${row.main_id}/template/date/${selectedYear}-${selectedMonth}-${selectedDay}/view/${tableView}/`;
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
                            templateUrl = `/ledger/api/character/${entityPk}/template/date/${selectedYear}-${selectedMonth}-${selectedDay}/view/${tableView}/`;
                            if (characteraltsShow) {
                                templateUrl += '?main=True';
                            }
                            $('#foot-'+ TableName +' .col-total-mining').html(formatAndColor(total_amount_mining));
                            $('#foot-'+ TableName +' .col-total-costs').html(formatAndColor(total_amount_costs));
                        } else {
                            templateUrl = `/ledger/api/${entityType}/${entityPk}/0/template/date/${selectedYear}-${selectedMonth}-${selectedDay}/view/${tableView}/?corp=true`;
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
    const target = $(this).attr('data-bs-target');
    console.log(target);
});
