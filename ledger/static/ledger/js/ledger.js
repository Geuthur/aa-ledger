/* global ledgersettings, load_or_create_Chart, setBillboardData */
/* eslint-disable */

var LedgerUrl, ChartUrl
var ActiveBillboardMonth, selectedMode;

const entityPk = ledgersettings.entity_pk;
const entityType = ledgersettings.entity_type;
const characteraltsShow = ledgersettings.altShow;
const overviewText = ledgersettings.overviewText;
const planetaryText = ledgersettings.planetaryText;

var monthText = getMonthName(selectedMonth);
var mainAlts = '';
// Check if altShow is true and append '?main=True' to the URLs
if (characteraltsShow) {
    mainAlts = '?main=True';
}

const barDropdownMode = document.getElementById('barDropdownMode');
const yearDropdown = document.getElementById('yearDropdown');
const monthDropdown = document.getElementById('monthDropdown');
const dayDropdown = document.getElementById('dayDropdown');

// Aktuelles Datumobjekt erstellen
const currentDate = new Date();

// Aktuelles Jahr und Monat abrufen
var selectedYear = currentDate.getFullYear();
var selectedMonth = currentDate.getMonth() + 1;
var selectedDay = 1;
var selectedviewMode = 'month';

function updateUrls() {
    LedgerUrl = `/ledger/api/${entityType}/${entityPk}/ledger/date/${selectedYear}-${selectedMonth}-${selectedDay}/view/${selectedviewMode}/${mainAlts}`;
    ChartUrl = `/ledger/api/${entityType}/${entityPk}/billboard/date/${selectedYear}-${selectedMonth}-${selectedDay}/view/${selectedviewMode}/${mainAlts}`;
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

function populateDays(selectedMonth) {
    const daysInMonth = new Date(selectedYear, selectedMonth, 0).getDate();

    // Clear existing options
    dayDropdown.innerHTML = '';

    // Populate the day dropdown with the correct number of days
    for (let day = 1; day <= daysInMonth; day++) {
        const listItem = document.createElement('li');
        const anchor = document.createElement('a');
        anchor.className = 'dropdown-item';
        anchor.href = '#';
        anchor.textContent = day;
        listItem.appendChild(anchor);
        dayDropdown.appendChild(listItem);
    }
}

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

function hideLoading() {
    $('#bar-loading').addClass('d-none');
    $('#chart-loading').addClass('d-none');
    $('#loadingIndicator').addClass('d-none');
}

function showLoading() {
    $('#bar-loading').removeClass('d-none');
    $('#chart-loading').removeClass('d-none');
    $('#loadingIndicator').removeClass('d-none');
}

function hideContainer() {
    $('#lookup').addClass('d-none');
    $('#ChartContainer').addClass('d-none');
    $('#rattingBarContainer').addClass('d-none');
    $('#workGaugeContainer').addClass('d-none');
}

function generateLedger(TableName, url) {
    return $.ajax({
        url: url,
        type: 'GET',
        success: function(data) {
            if (window[TableName + 'Table']) {
                $('#ratting').DataTable().destroy();
            }
            hideLoading();
            const char_name = data[0].ratting[0]?.main_name || 'No Data';
            const char_id = data[0].ratting[0]?.main_id || '0';
            const total_amount = data[0].total.total_amount;
            const total_amount_ess = data[0].total.total_amount_ess;
            const total_amount_others = data[0].total.total_amount_others;
            const total_amount_mining = data[0].total.total_amount_mining;
            const total_amount_combined = data[0].total.total_amount_all;
            const total_amount_costs = data[0].total.total_amount_costs;

            if (entityPk > 0 && !characteraltsShow && entityType === 'character') {
                $('#lookup').removeClass('d-none');
                // Daten direkt in die HTML-Elemente einfügen
                $('#portrait').html('<img width="256" height="256" class="rounded" src="https://images.evetech.net/characters/' + char_id + '/portrait?size=256">');
                $('#character_name').text(char_name);
                $('#amount_ratting').html(formatAndColor(total_amount));
                $('#amount_ess').html(formatAndColor(total_amount_ess));
                $('#amount_mining').html(formatAndColor(total_amount_mining));
                $('#amount_misc').html(formatAndColor(total_amount_others));
                $('#amount_costs').html(formatAndColor(total_amount_costs));
                $('#amount_summary').html(formatAndColor(total_amount_combined));
                $('#planetary_interaction').html(`
                    <a href="/ledger/planetary_ledger/${entityPk}/">
                        <image src="/static/ledger/images/pi.png"
                            title="${planetaryText}"
                            height="256" data-tooltip-toggle="ledger-tooltip" data-bs-placement="top">
                    </a>
                `);
                $('#get_template').html(`
                    <button
                        class="btn btn-sm btn-info btn-square" id="button-${TableName}"
                        data-bs-toggle="modal"
                        data-bs-target="#modalViewCharacterContainer"
                        aria-label="${char_name}"
                        data-ajax_url="/ledger/api/${entityType}/${char_id}/template/date/${selectedYear}-${selectedMonth}-${selectedDay}/view/${selectedviewMode}/"
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
                window[table] = $('#ratting').DataTable({
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
                                                    id="lookup"
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
                                    chartemplateUrl = `/ledger/api/character/${row.main_id}/template/date/${selectedYear}-${selectedMonth}-${selectedDay}/view/${selectedviewMode}/`;
                                } else {
                                    chartemplateUrl = `/ledger/api/${entityType}/${entityPk}/${row.main_id}/template/date/${selectedYear}-${selectedMonth}-${selectedDay}/view/${selectedviewMode}/`;
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
                            targets: entityType === 'character' ? [6] : [4],
                            className: 'text-end',
                        },
                    ],
                    footerCallback: function (_, data, __, ___, ____) {
                        if (data.length === 0) {
                            $('#foot .col-total-amount').html('');
                            $('#foot .col-total-ess').html('');
                            $('#foot .col-total-others').html('');
                            $('#foot .col-total-gesamt').html('');
                            $('#foot .col-total-button').html('').removeClass('text-end');

                            if (entityType === 'character') {
                                $('#foot .col-total-mining').html('');
                                $('#foot .col-total-costs').html('');
                            }
                            return;
                        }

                        var templateUrl = '';
                        if (entityType === 'character') {
                            templateUrl = `/ledger/api/character/${entityPk}/template/date/${selectedYear}-${selectedMonth}-${selectedDay}/view/${selectedviewMode}/`;
                            if (characteraltsShow) {
                                templateUrl += '?main=True';
                            }
                            $('#foot .col-total-mining').html(formatAndColor(total_amount_mining));
                            $('#foot .col-total-costs').html(formatAndColor(total_amount_costs));
                        } else {
                            templateUrl = `/ledger/api/${entityType}/${entityPk}/0/template/date/${selectedYear}-${selectedMonth}-${selectedDay}/view/${selectedviewMode}/?corp=true`;
                        }

                        $('#foot .col-total-amount').html(formatAndColor(total_amount));
                        $('#foot .col-total-ess').html(formatAndColor(total_amount_ess));
                        $('#foot .col-total-others').html(formatAndColor(total_amount_others));
                        $('#foot .col-total-gesamt').html(formatAndColor(total_amount_combined));

                        $('#foot .col-total-button').html(`
                            <button
                                class="btn btn-sm btn-info btn-square"
                                data-bs-toggle="modal"
                                data-bs-target="#modalViewCharacterContainer"
                                data-ajax_url="${templateUrl}">
                                <span class="fas fa-info"></span></button>
                        `).addClass('text-end');
                    },
                    initComplete: function() {
                        $('#foot').show();
                        $('#ratting').removeClass('d-none');

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
                $('#ratting').DataTable().destroy();
                hideLoading();
                $('#errorHandler').removeClass('d-none');
                $('.dropdown-toggle').attr('disabled', true);
                $('.overview').attr('disabled', true);
            }
        }
    });
}

document.addEventListener('DOMContentLoaded', function () {
    // Initialize the URLs
    updateUrls();

    setBillboardData(ChartUrl, 'Ledger');
    generateLedger('Ledger', LedgerUrl);
    populateDays(selectedMonth);

    barDropdownMode.addEventListener('click', function(event) {
        selectedMode = event.target.textContent;
        var div = 'rattingBar';
        if (selectedMode === hourlyText) {
            var data = BillboardHourly.rattingbar;
        } else {
            var data = BillboardMonth.rattingbar;
        }
        const success = load_or_create_Chart(div=div, data=data, id='Ledger', chart='bar');
        if (success) {
            $('#barTitle').text('Ledger ' + selectedMode);
            console.log('Chart loaded successfully');
        } else {
            console.log('Failed to load chart');
        }
    });

    yearDropdown.addEventListener('click', function(event) {
        if (event.target && event.target.matches('a.dropdown-item')) {
            // Remove the active class from all items
            const items = yearDropdown.querySelectorAll('a.dropdown-item');
            items.forEach(item => item.classList.remove('active'));
            const monthitems = monthDropdown.querySelectorAll('a.dropdown-item');
            monthitems.forEach(item => item.classList.remove('active'));
            const dayitems = dayDropdown.querySelectorAll('a.dropdown-item');
            dayitems.forEach(item => item.classList.remove('active'));

            // Add the active class to the selected item
            event.target.classList.add('active');
            // Set the text content
            $('#yearDropDownButton').text(event.target.textContent);
            $('#monthDropDownButton').text("Month");
            $('#dayDropDownButton').text("Day");
        }
        selectedYear = event.target.dataset.bsYearId;
        selectedviewMode = 'year';
        showLoading('Ledger');
        hideContainer('Ledger');

        if (entityPk === 0 || (entityPk > 0 && characteraltsShow && entityType !== 'character')) {
            window['LedgerTable'].clear().draw();
            $('#foot').hide();
        }

        // Update URL Data
        updateUrls();

        // DataTable neu laden mit den Daten des ausgewählten Monats
        setBillboardData(ChartUrl, 'Ledger');
        generateLedger('Ledger', LedgerUrl);
    });

    monthDropdown.addEventListener('click', function(event) {
        if (event.target && event.target.matches('a.dropdown-item')) {
            // Remove the active class from all items
            const items = monthDropdown.querySelectorAll('a.dropdown-item');
            items.forEach(item => item.classList.remove('active'));
            const dayitems = dayDropdown.querySelectorAll('a.dropdown-item');
            dayitems.forEach(item => item.classList.remove('active'));

            // Add the active class to the selected item
            event.target.classList.add('active');
            // Set the text content
            $('#monthDropDownButton').text(event.target.textContent);
            $('#dayDropDownButton').text("Day");
        }
        selectedMonth = event.target.dataset.bsMonthId;
        showLoading('Ledger');
        hideContainer('Ledger');

        if (entityPk === 0 || (entityPk > 0 && characteraltsShow && entityType !== 'character')) {
            window['LedgerTable'].clear().draw();
            $('#foot').hide();
            populateDays(selectedMonth);
        }
        selectedviewMode = 'month';

        // Update URL Data
        updateUrls();

        // DataTable neu laden mit den Daten des ausgewählten Monats
        setBillboardData(ChartUrl, 'Ledger');
        generateLedger('Ledger', LedgerUrl);
    });

    dayDropdown.addEventListener('click', function(event) {
        if (event.target && event.target.matches('a.dropdown-item')) {
            // Remove the active class from all items
            const items = dayDropdown.querySelectorAll('a.dropdown-item');
            items.forEach(item => item.classList.remove('active'));

            // Add the active class to the selected item
            event.target.classList.add('active');
            // Set the text content
            $('#dayDropDownButton').text(event.target.textContent);
        }

        selectedDay = event.target.textContent;
        selectedviewMode = 'day';

        // Update URL Data
        updateUrls();

        // DataTable neu laden mit den Daten des ausgewählten Monats
        setBillboardData(ChartUrl, 'Ledger');
        generateLedger('Ledger', LedgerUrl);
    });
});
