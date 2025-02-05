/* global planetarySettings */
/* global bootstrap */

document.addEventListener('DOMContentLoaded', function() {
    var csrfToken = planetarySettings.csrfToken;
    var urlAlarm = planetarySettings.switchAlarmUrl;
    var url = planetarySettings.planetaryUrl;
    var switchAlarmText = planetarySettings.switchAlarmText;
    var switchAlarm = planetarySettings.switchAlarm;
    var switchAlarmAll = planetarySettings.switchAlarmAll;
    var alarmActivated = planetarySettings.alarmActivated;
    var alarmDeactivated = planetarySettings.alarmDeactivated;
    var characterPk = planetarySettings.characterPk;

    function switchAlarmUrl(characterId, planetId) {
        return urlAlarm
            .replace('1337', characterId)
            .replace('1337', planetId);
    }

    var confirmModal = document.getElementById('confirmModal');
    var confirmRequest = document.getElementById('confirm-request');
    var finalizeActionButton = document.getElementById('finalizeActionButton');

    confirmModal.addEventListener('show.bs.modal', function (event) {
        var button = event.relatedTarget;
        var confirmText = button.getAttribute('data-confirm-text');
        var formId = button.getAttribute('data-form-id');

        confirmRequest.textContent = confirmText;

        finalizeActionButton.onclick = function () {
            document.getElementById(formId).submit();
            var modal = bootstrap.Modal.getInstance(confirmModal);
            modal.hide();
        };
    });

    // Initialize DataTable
    var table = $('#planets-details').DataTable({
        'order': [[4, 'desc']], // Adjust the column index if needed
        'pageLength': 25,
        'columnDefs': [
            { 'orderable': false, 'targets': 'no-sort' }
        ]
    });

    // Fetch data using AJAX
    $.ajax({
        url: url,
        method: 'GET',
        dataType: 'json',
        success: function(data) {
            const characterIds = new Set();

            data.forEach(item => {
                characterIds.add(item.character_id);
                const row = [];

                const viewFactoryUrl = `/ledger/api/character/${item.character_id}/planetary/${item.planet_id}/factory/`;
                const viewExtractorUrl = `/ledger/api/character/${item.character_id}/planetary/${item.planet_id}/extractor/`;

                // Character
                const characterCell = `
                    <td>
                        <img src="https://images.evetech.net/characters/${item.character_id}/portrait?size=32" class="rounded-circle" style="margin-right: 5px;">
                        ${item.character_name}
                    </td>
                `;

                // Planet Type
                const planetTypeCell = `
                    <td>
                        <img src="https://images.evetech.net/types/${item.planet_type_id}/icon?size=32" class="rounded-circle" style="margin-right: 5px;" data-tooltip-toggle="planetary" title="${item.planet}">
                        ${item.planet}
                        <i class="fa-solid fa-bullhorn" style="margin-left: 5px; color: ${item.alarm ? 'green' : 'red'};" title="${item.alarm ? alarmActivated : alarmDeactivated}" data-tooltip-toggle="planetary"></i>
                    </td>
                `;

                // Upgrade Level
                const upgradeLevelCell = `<td>${item.upgrade_level}</td>`;

                // Products
                const productsCell = `
                    <td>
                        ${Object.values(item.products.processed).map(product => `<img src="https://images.evetech.net/types/${product.id}/icon?size=32" data-tooltip-toggle="planetary" title="${product.name}">`).join(' ')}
                    </td>
                    <button class="btn btn-primary btn-sm btn-square"
                        data-bs-toggle="modal"
                        data-bs-target="#modalViewFactoryContainer"
                        data-ajax_factory="${viewFactoryUrl}"
                        title="${row.main_name}" data-tooltip-toggle="ledger-tooltip" data-bs-placement="left">
                        <span class="fas fa-info"></span>
                    </button>
                `;

                // Extractors
                let extractorsCell = '<td>No Extractors</td>';
                if (Object.values(item.extractors).length > 0) {
                    let totalInstallTime = 0;
                    let totalExpiryTime = 0;
                    let currentTime = new Date().getTime();
                    let extractorCount = Object.values(item.extractors).length;

                    Object.values(item.extractors).forEach(extractor => {
                        totalInstallTime += new Date(extractor.install_time).getTime();
                        totalExpiryTime += new Date(extractor.expiry_time).getTime();
                    });

                    let averageInstallTime = totalInstallTime / extractorCount;
                    let averageExpiryTime = totalExpiryTime / extractorCount;

                    const totalDuration = averageExpiryTime - averageInstallTime;
                    const elapsedDuration = currentTime - averageInstallTime;
                    const progressPercentage = Math.min(Math.max((elapsedDuration / totalDuration) * 100, 0), 100);

                    let extractorIcons = Object.values(item.extractors).map(extractor => {
                        let iconUrl = getIconUrl(extractor.item_id);
                        return `<img src="${iconUrl}" data-tooltip-toggle="planetary" title="${extractor.item_name}">`;
                    }).join('');

                    extractorsCell = `
                        <td>
                            <div style="display: flex; align-items: center;">
                                <div class="progress-outer" style="flex-grow: 1; margin-right: 10px;">
                                    <div class="progress">
                                        <div class="progress-bar progress-bar-warning progress-bar-striped active" role="progressbar" style="width: ${progressPercentage}%; box-shadow: -1px 10px 10px rgba(240, 173, 78, 0.7);" aria-valuenow="${progressPercentage}" aria-valuemin="0" aria-valuemax="100"></div>
                                        <div class="progress-value">${progressPercentage.toFixed(0)}%</div>
                                    </div>
                                </div>
                                ${extractorIcons}
                                <button class="btn btn-primary btn-sm btn-square"
                                    data-bs-toggle="modal"
                                    data-bs-target="#modalViewExtractorContainer"
                                    data-ajax_extractor="${viewExtractorUrl}"
                                    title="${row.main_name}" data-tooltip-toggle="ledger-tooltip" data-bs-placement="left">
                                    <span class="fas fa-info"></span>
                                </button>
                            </div>
                        </td>
                    `;
                }

                // Status
                const statusCell = `
                    <td>
                        <img src="/static/ledger/images/${item.expired ? 'red' : 'green'}.png" style="width: 24px; height: 24px;" title="${item.expired ? 'Expired' : 'Active'}" data-tooltip-toggle="planetary">
                    </td>
                `;

                // Last Updated
                const lastUpdatedCell = `<td>${new Date(item.last_update).toLocaleString()}</td>`;

                // Actions
                const actionsCell = `
                    <td>
                        <form class="text-end" method="post" action="${switchAlarmUrl(item.character_id, item.planet_id)}" id="switchAlarmForm${item.character_id}_${item.planet_id}">
                            ${csrfToken}
                            <input type="hidden" name="character_pk" value="${characterPk}">
                            <button type="button" class="btn btn-primary btn-sm btn-square" data-bs-toggle="modal" data-tooltip-toggle="planetary" title="${switchAlarm}" data-bs-target="#confirmModal" data-confirm-text="${switchAlarmText} \n${item.character_name} - ${item.planet}?" data-form-id="switchAlarmForm${item.character_id}_${item.planet_id}">
                                <span class="fas fa-bullhorn"></span>
                            </button>
                        </form>
                    </td>
                `;

                row.push(characterCell, planetTypeCell, upgradeLevelCell, productsCell, extractorsCell, statusCell, lastUpdatedCell, actionsCell);
                table.row.add(row).draw();
            });

            // Add "Switch All Alarms" button if data exists
            if (data.length > 0) {
                const switchAllAlarmsButton = document.createElement('button');
                switchAllAlarmsButton.textContent = switchAlarmAll;
                switchAllAlarmsButton.className = 'btn btn-primary';
                switchAllAlarmsButton.style.marginTop = '10px';
                switchAllAlarmsButton.title = switchAlarm;

                const switchAllAlarmsForm = document.createElement('form');
                switchAllAlarmsForm.method = 'post';
                switchAllAlarmsForm.action = switchAlarmUrl(characterPk, 0);
                switchAllAlarmsForm.id = 'switchAllAlarmsForm';
                switchAllAlarmsForm.className = 'd-inline';
                switchAllAlarmsForm.innerHTML = csrfToken +
                    '<input type="hidden" name="character_pk" value="' + characterPk + '">' +
                    '<button type="button" class="btn btn-primary btn-sm btn-square" data-bs-toggle="modal" data-tooltip-toggle="planetary" title="'+ switchAlarm +'" data-bs-target="#confirmModal" data-confirm-text="' + switchAlarmText + '?" data-form-id="switchAllAlarmsForm">' + switchAllAlarmsButton.textContent + '</button>';

                const tableContainer = document.querySelector('#planets-details').parentElement;
                const switchAllAlarmsContainer = document.createElement('div');
                switchAllAlarmsContainer.className = 'switch-all-alarms-container';
                switchAllAlarmsContainer.appendChild(switchAllAlarmsForm);
                tableContainer.appendChild(switchAllAlarmsContainer);
            }

            // Reinitialize tooltips on draw
            table.on('draw', function () {
                $('[data-tooltip-toggle="planetary"]').tooltip({
                    trigger: 'hover',
                });
            });
            // Init tooltips

            $('[data-tooltip-toggle="planetary"]').tooltip({
                trigger: 'hover',
            });
        },
        error: function(error) {
            console.error('Error fetching data:', error);
        }
    });
});

function getIconUrl(typeId) {
    return `https://images.evetech.net/types/${typeId}/icon?size=32`;
}
