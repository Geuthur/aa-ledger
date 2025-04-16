/* global ledgersettings, load_or_create_Chart, initCharts, updateUrls, handleDropdownClick, populateDays, showLoading, hideContainer, initTooltip, formatAndColor, hideLoading */

var LedgerUrl;

const entityPk = ledgersettings.entity_pk;
const entityType = ledgersettings.entity_type;

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

let total_amount = 0;
let total_amount_ess = 0;
let total_amount_others = 0;
let total_amount_combined = 0;

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

            const char_name = data.ratting?.main_name || 'No Data';
            const char_id = data.ratting?.main_id || '0';
            const total_amount = data.total.total_amount;
            const total_amount_ess = data.total.total_amount_ess;
            const total_amount_others = data.total.total_amount_others;
            const total_amount_costs = data.total.total_amount_costs;
            const total_amount_combined = data.total.total_amount_all;

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

                            var imageHTML =`
                                <img
                                    src='${imageUrl}'
                                    class="rounded-circle"
                                > ${data}
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
                        $('#foot .col-total-costs').html('');
                        $('#foot .col-total-button').html('').removeClass('text-end');
                        return;
                    }

                    var templateUrl = `/ledger/api/${entityType}/${entityPk}/template/date/${state.selectedYear}-${state.selectedMonth}-${state.selectedDay}/view/${state.selectedviewMode}/`;

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
        LedgerUrl = updateUrls(entityType, entityPk, state.selectedYear, state.selectedMonth, state.selectedDay, state.selectedviewMode);
        generateLedger('Ledger', LedgerUrl);
    };

    updateCallback();
    populateDays(state.selectedYear, state.selectedMonth, dayDropdown);

    yearDropdown.addEventListener('click', event => handleDropdownClick(event, 'year', state, updateCallback));
    monthDropdown.addEventListener('click', event => handleDropdownClick(event, 'month', state, updateCallback));
    dayDropdown.addEventListener('click', event => handleDropdownClick(event, 'day', state, updateCallback));
});
