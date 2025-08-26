/* global planetarySettings, bootstrap */

$(document).ready(() => {
    var switchAlarmText = planetarySettings.switchAlarmText;
    var switchAlarm = planetarySettings.switchAlarm;
    var alarmActivated = planetarySettings.alarmActivated;
    var alarmDeactivated = planetarySettings.alarmDeactivated;
    var viewSwitchAlarmUrl = planetarySettings.viewSwitchAlarmUrl;

    function viewFactoryUrl(characterId, planetId) {
        return planetarySettings.viewFactoryUrl.replace('1337', characterId).replace('1337', planetId);
    }

    function viewExtractorUrl(characterId, planetId) {
        return planetarySettings.viewExtractorUrl.replace('1337', characterId).replace('1337', planetId);
    }



    // Initialize DataTable
    const PlanetaryTable = $('#planets-details').DataTable({
        ajax: {
            url: planetarySettings.planetaryUrl,
            dataSrc: '',
            cache: false
        },
        columns: [
            {
                data: 'character_name',
                render: function(data, type, row) {
                    return `
                        <img src="https://images.evetech.net/characters/${row.character_id}/portrait?size=32" class="rounded-circle" style="margin-right: 5px;">
                        ${data}
                    `;
                }
            },
            {
                data: 'planet',
                render: function(data, type, row) {
                    return `
                        <img src="https://images.evetech.net/types/${row.planet_type_id}/icon?size=32" class="rounded-circle" style="margin-right: 5px;" data-tooltip-toggle="ledger" title="${row.planet}">
                        ${data}
                        <i class="fa-solid fa-bullhorn" style="margin-left: 5px; color: ${row.alarm ? 'green' : 'red'};" title="${row.alarm ? alarmActivated : alarmDeactivated}" data-tooltip-toggle="ledger"></i>
                    `;
                }
            },
            {
                data: 'upgrade_level'
            },
            {
                data: 'products',
                render: function(data, type, row) {
                    return Object.values(data.processed).map(product => `
                        <img src="https://images.evetech.net/types/${product.id}/icon?size=32" data-tooltip-toggle="ledger" title="${product.name}">
                    `).join(' ') + `
                    <button class="btn btn-primary btn-sm btn-square"
                        data-bs-toggle="modal"
                        data-bs-target="#modalViewFactoryContainer"
                        data-ajax_factory="${viewFactoryUrl(row.character_id, row.planet_id)}"
                        data-tooltip-toggle="ledger"
                        data-bs-placement="left"
                        title="${row.character_name} - ${row.planet}"
                        >
                        <span class="fas fa-info"></span>
                    </button>`;
                }
            },
            {
                data: 'percentage'
            },
            {
                data: 'extractors',
                render: function(data, type, row) {
                    return Object.values(row.products.raw).map(product => `
                        <img src="https://images.evetech.net/types/${product.id}/icon?size=32" data-tooltip-toggle="ledger" title="${product.name}">
                    `).join(' ') + `
                    <button class="btn btn-primary btn-sm btn-square"
                        data-bs-toggle="modal"
                        data-bs-target="#modalViewExtractorContainer"
                        data-ajax_extractor="${viewExtractorUrl(row.character_id, row.planet_id)}"
                        data-tooltip-toggle="ledger"
                        data-bs-placement="left"
                        title="${row.character_name} - ${row.planet}"
                        >
                        <span class="fas fa-info"></span>
                    </button>`;
                }
            },
            {
                data: 'status',
                render: function(data, type, row) {
                    return `
                        <img src="/static/ledger/images/${row.expired ? 'red' : 'green'}.png" style="width: 24px; height: 24px;" title="${row.expired ? 'Expired' : 'Active'}" data-tooltip-toggle="ledger">
                    `;
                }
            },
            {
                data: 'last_update',
                render: function(data, type, row) {
                    if (data === null) {
                        return `<span class="text-warning" data-tooltip-toggle="ledger">Not updated yet</span>`;
                    }
                    return new Date(data).toLocaleString();
                }

            },
            {
                data: 'actions',
                render: function(data, type, row) {
                    return `
                        <button type="button" class="btn btn-primary btn-sm btn-square me-2" data-bs-toggle="modal" data-tooltip-toggle="ledger" data-character-id="${row.character_id}" data-planet-id="${row.planet_id}" data-title="${switchAlarm}" data-text="${switchAlarmText} \n${row.character_name} - ${row.planet}?" data-bs-target="#ledger-planetary-confirm" data-action="${viewSwitchAlarmUrl}" aria-label="Toggle Alarm">
                            <span class="fas fa-bullhorn"></span>
                        </button>
                    `;
                }
            }
        ],
        columnDefs: [
            {
                orderable: false,
                targets: 'no-sort',
            }
        ],
        order: [
            [4, 'desc']
        ],
        pageLength: 25,
        initComplete: function() {
            $('[data-tooltip-toggle="ledger"]').tooltip({
                trigger: 'hover',
            });
            $('#ledger-index').addClass('show');
        },
        drawCallback: function() {
            $('[data-tooltip-toggle="ledger"]').tooltip({
                trigger: 'hover',
            });
        }
    });

    // Make PlanetaryTable globally accessible
    window.PlanetaryTable = PlanetaryTable;
});
