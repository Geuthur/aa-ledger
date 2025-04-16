/* global ledgersettings, load_or_create_Chart, initCharts, updateUrls, handleDropdownClick, populateDays, showLoading, hideContainer, initTooltip, formatAndColor, hideLoading */

var LedgerUrl;

const entityPk = ledgersettings.entity_pk;
const entityType = ledgersettings.entity_type;
const characteraltsShow = ledgersettings.altShow;
const overviewText = ledgersettings.overviewText;
const planetaryText = ledgersettings.planetaryText;

var singleView = '';
// Check if singleView is true and append '?single=True' to the URLs
if (characteraltsShow) {
    singleView = '?single=True';
}

const yearDropdown = document.getElementById('yearDropdown');
const monthDropdown = document.getElementById('monthDropdown');
const dayDropdown = document.getElementById('dayDropdown');

// Aktuelles Datumobjekt erstellen
const currentDate = new Date();
const state = {
    selectedYear: currentDate.getFullYear(),
    selectedMonth: currentDate.getMonth() + 1,
    selectedDay: 1,
    selectedviewMode: 'month',
    translations: window.translations,
};

function generateLedger(TableName, url) {
    return $.ajax({
        url: url,
        type: 'GET',
        success: function(data) {
            if (window[TableName + 'Table']) {
                $('#ratting').DataTable().destroy();
            }
            hideLoading();

            try {
                initCharts(data.billboard);
            } catch (error) {
                console.error('Error initializing charts:', error);
            }

            const char_name = data.ratting[0]?.main_name || 'No Data';
            const char_id = data.ratting[0]?.main_id || '0';
            const total_amount = data.total.total_amount;
            const total_amount_ess = data.total.total_amount_ess;
            const total_amount_others = data.total.total_amount_others;
            const total_amount_mining = data.total.total_amount_mining;
            const total_amount_combined = data.total.total_amount_all;
            const total_amount_costs = data.total.total_amount_costs;

            if (entityPk > 0 && characteraltsShow) {
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
                    <a href="/ledger/planetary_ledger/${entityPk}/?single=true">
                        <image src="/static/ledger/images/pi.png"
                            title="${planetaryText}"
                            height="256" data-tooltip-toggle="ledger-tooltip" data-bs-placement="top">
                    </a>
                `);
                $('#get_template').html(`
                    <button
                        class="btn btn-primary btn-sm btn-square" id="button-${TableName}"
                        data-bs-toggle="modal"
                        data-bs-target="#modalViewCharacterContainer"
                        aria-label="${char_name}"
                        data-ajax_url="/ledger/api/${entityType}/${char_id}/template/date/${state.selectedYear}-${state.selectedMonth}-${state.selectedDay}/view/${state.selectedviewMode}/?character_id=${char_id}"
                        title="${char_name}"
                        data-tooltip-toggle="ledger-tooltip" data-bs-placement="right">
                        <span class="fas fa-info"></span>
                    </button>
                `);
                const infobutton = document.getElementById('button-'+ TableName +'');
                if (!data.ratting[0]?.main_name) {
                    infobutton.classList.add('disabled');
                }
                initTooltip();
            } else {
                var table = TableName + 'Table';
                window[table] = $('#ratting').DataTable({
                    data: data.ratting,
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
                                    imageUrl += 'characters/0/portrait?size=32'; // Beispiel für ein Platzhalterbild
                                }

                                var imageHTML = `
                                    <img src="${imageUrl}"
                                        class="rounded-circle"
                                        title="${data}"
                                        data-tooltip-toggle="ledger-tooltip" data-bs-placement="right"
                                        height="30"> ${data}
                                    <a href="/ledger/character_ledger/${row.main_id}/?single=True">
                                        <button
                                            class="btn btn-primary btn-sm btn-square"
                                            id="lookup"
                                            title="${overviewText}"
                                            data-tooltip-toggle="ledger-tooltip" data-bs-placement="right">
                                            <span class="fas fa-search"></span>
                                        </button>
                                    </a>
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
                        {   data: 'total_amount_mining',
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
                        {   data: 'total_amount_costs',
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
                                var chartemplateUrl = `/ledger/api/${entityType}/${entityPk}/template/date/${state.selectedYear}-${state.selectedMonth}-${state.selectedDay}/view/${state.selectedviewMode}/`;
                                if (entityType === 'character') {
                                    chartemplateUrl += `?character_id=${row.main_id}`;
                                } else if (entityType === 'corporation') {
                                    chartemplateUrl += `?main_character_id=${row.main_id}`;
                                } else if (entityType === 'alliance') {
                                    chartemplateUrl += `?corporation_id=${row.main_id}`;
                                }

                                return `
                                    <button class="btn btn-primary btn-sm btn-square"
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
                            $('#foot .col-total-mining').html('');
                            $('#foot .col-total-costs').html('');
                            return;
                        }

                        var templateUrl = `/ledger/api/${entityType}/${entityPk}/template/date/${state.selectedYear}-${state.selectedMonth}-${state.selectedDay}/view/${state.selectedviewMode}/`;
                        if (entityType === 'character') {
                            $('#foot .col-total-mining').html(formatAndColor(total_amount_mining));
                            $('#foot .col-total-costs').html(formatAndColor(total_amount_costs));
                        }

                        $('#foot .col-total-amount').html(formatAndColor(total_amount));
                        $('#foot .col-total-ess').html(formatAndColor(total_amount_ess));
                        $('#foot .col-total-others').html(formatAndColor(total_amount_others));
                        $('#foot .col-total-costs').html(formatAndColor(total_amount_costs));
                        $('#foot .col-total-gesamt').html(formatAndColor(total_amount_combined));

                        $('#foot .col-total-button').html(`
                            <button
                                class="btn btn-primary btn-sm btn-square"
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
                $('#errorHandler').text('You have no permission to view this page');
            } else if (xhr.status === 404) {
                $('#errorHandler').text('No data found');
            } else {
                $('#errorHandler').text('An error occurred');
            }
            $('#ratting').DataTable().destroy();
            hideLoading();
            $('#errorHandler').removeClass('d-none');
            $('.dropdown-toggle').attr('disabled', true);
            $('.administration').attr('disabled', true);
        }
    });
}

document.addEventListener('DOMContentLoaded', function () {
    const updateCallback = () => {
        LedgerUrl = updateUrls(entityType, entityPk, state.selectedYear, state.selectedMonth, state.selectedDay, state.selectedviewMode, singleView);
        generateLedger('Ledger', LedgerUrl);
    };

    updateCallback();
    populateDays(state.selectedYear, state.selectedMonth, dayDropdown);

    yearDropdown.addEventListener('click', event => handleDropdownClick(event, 'year', state, updateCallback));
    monthDropdown.addEventListener('click', event => handleDropdownClick(event, 'month', state, updateCallback));
    dayDropdown.addEventListener('click', event => handleDropdownClick(event, 'day', state, updateCallback));
});
