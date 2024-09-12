/* global planetarySettings */
/* global bootstrap */

document.addEventListener('DOMContentLoaded', function() {
    var csrfToken = planetarySettings.csrfToken;
    var urlAlarm = planetarySettings.switchAlarmUrl;
    var url = planetarySettings.planetaryUrl;
    var switchAlarmText = planetarySettings.switchAlarmText;
    var switchAlarm = planetarySettings.switchAlarm;
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

                // Character
                const characterCell = `
                    <td>
                        <img src="https://images.evetech.net/characters/${item.character_id}/portrait?size=32" class="rounded-circle" style="margin-right: 5px; width: 32px; height: 32px;">
                        ${item.character_name}
                    </td>
                `;

                // Planet Type
                const planetTypeCell = `
                    <td>
                        <img src="https://images.evetech.net/types/${item.planet_type_id}/icon?size=32" class="rounded-circle" style="margin-right: 5px; width: 24px; height: 24px;">
                        ${item.planet}
                        <i class="fa-solid fa-bullhorn" style="margin-left: 5px; color: ${item.alarm ? 'green' : 'red'};" title="${item.alarm ? alarmActivated : alarmDeactivated}" data-tooltip-toggle="tooltip"></i>
                    </td>
                `;

                // Upgrade Level
                const upgradeLevelCell = `<td>${item.upgrade_level}</td>`;

                // Products
                const productsCell = `
                    <td>
                        ${Object.values(item.products).map(product => `<img src="https://images.evetech.net/types/${product.id}/icon?size=32" data-tooltip-toggle="tooltip" title="${product.name}">`).join(' ')}
                    </td>
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

                    extractorsCell = `
                        <td>
                            <div style="display: flex; align-items: center;">
                                <div class="progress-outer" style="flex-grow: 1; margin-right: 10px;">
                                    <div class="progress">
                                        <div class="progress-bar progress-bar-warning progress-bar-striped active" role="progressbar" style="width: ${progressPercentage}%; box-shadow: -1px 10px 10px rgba(240, 173, 78, 0.7);" aria-valuenow="${progressPercentage}" aria-valuemin="0" aria-valuemax="100"></div>
                                        <div class="progress-value">${progressPercentage.toFixed(0)}%</div>
                                    </div>
                                </div>
                                <button class="btn btn-primary btn-sm btn-square" style="margin-left: 5px;" data-bs-toggle="modal" data-bs-target="#extractorInfoModal" data-character-id="${item.character_id}" data-character-name="${item.character_name}" data-planet="${item.planet}" data-extractors='${JSON.stringify(item.extractors)}' onclick="showExtractorInfoModal(this)">                                    <span class="fas fa-info"></span>
                                </button>
                            </div>
                        </td>
                    `;
                }

                // Status
                const statusCell = `
                    <td>
                        <img src="/static/ledger/images/${item.expired ? 'red' : 'green'}.png" style="width: 24px; height: 24px;" title="${item.expired ? 'Expired' : 'Active'}" data-tooltip-toggle="tooltip">
                    </td>
                `;

                // Last Updated
                const lastUpdatedCell = `<td>${new Date(item.last_update).toLocaleString()}</td>`;

                // Actions
                const actionsCell = `
                    <td class="text-end">
                        <form class="d-inline" method="post" action="${switchAlarmUrl(item.character_id, item.planet_id)}" id="switchAlarmForm${item.character_id}_${item.planet_id}">
                            ${csrfToken}
                            <input type="hidden" name="character_pk" value="${characterPk}">
                            <button type="button" class="btn btn-primary btn-sm btn-square" data-bs-toggle="modal" data-tooltip-toggle="tooltip" title="${switchAlarm}" data-bs-target="#confirmModal" data-confirm-text="${switchAlarmText} for ${item.character_name} - ${item.planet}?" data-form-id="switchAlarmForm${item.character_id}_${item.planet_id}">
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
                switchAllAlarmsButton.textContent = 'Switch All Alarms';
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
                    '<button type="button" class="btn btn-primary btn-sm btn-square" data-bs-toggle="modal" data-tooltip-toggle="tooltip" title="'+ switchAlarm +'" data-bs-target="#confirmModal" data-confirm-text="' + switchAlarmText + '?" data-form-id="switchAllAlarmsForm">' + switchAllAlarmsButton.textContent + '</button>';

                const tableContainer = document.querySelector('#planets-details').parentElement;
                const switchAllAlarmsContainer = document.createElement('div');
                switchAllAlarmsContainer.className = 'switch-all-alarms-container';
                switchAllAlarmsContainer.appendChild(switchAllAlarmsForm);
                tableContainer.appendChild(switchAllAlarmsContainer);
            }

            // Reinitialize tooltips on draw
            table.on('draw', function () {
                $('[data-tooltip-toggle="tooltip"]').tooltip();
            });
            // Init tooltips
            $('[data-tooltip-toggle="tooltip"]').tooltip();
        },
        error: function(error) {
            console.error('Error fetching data:', error);
        }
    });
});

function showExtractorInfoModal(button) {
    const characterId = button.getAttribute('data-character-id');
    const characterName = button.getAttribute('data-character-name');
    const planet = button.getAttribute('data-planet');
    const extractors = JSON.parse(button.getAttribute('data-extractors'));

    const modalTitle = document.querySelector('#extractorInfoModalLabel');
    modalTitle.textContent = `Extractor Information - ${characterName} - ${planet}`;

    const modalBody = document.querySelector('#extractorInfoModal .modal-body');
    modalBody.innerHTML = ''; // Clear previous content

    // Create table
    const table = document.createElement('table');
    table.className = 'table table-striped';

    // Create table header
    const thead = document.createElement('thead');
    thead.innerHTML = `
        <tr>
            <th>Product</th>
            <th>Install Time</th>
            <th>Expiry Time</th>
            <th>Progress</th>
        </tr>
    `;
    table.appendChild(thead);

    // Create table body
    const tbody = document.createElement('tbody');

    const currentTime = new Date().getTime();
    Object.values(extractors).forEach(extractor => {
        const installTime = new Date(extractor.install_time).getTime();
        const expiryTime = new Date(extractor.expiry_time).getTime();
        const totalDuration = expiryTime - installTime;
        const elapsedDuration = currentTime - installTime;
        const progressPercentage = Math.min(Math.max((elapsedDuration / totalDuration) * 100, 0), 100);

        const row = document.createElement('tr');
        row.innerHTML = `
            <td><span class="fas fa-cube"></span> ${extractor.product_name}</td>
            <td>${new Date(extractor.install_time).toLocaleString()}</td>
            <td>${new Date(extractor.expiry_time).toLocaleString()}</td>
            <td>
                <div class="progress" style="position: relative;">
                    <div class="progress-bar progress-bar-warning progress-bar-striped active" role="progressbar" style="width: ${progressPercentage}%; box-shadow: -1px 3px 5px rgba(0, 180, 231, 0.9);" aria-valuenow="${progressPercentage}" aria-valuemin="0" aria-valuemax="100"></div>
                    <div class="progress-value" style="position: absolute; width: 100%; text-align: center;">${progressPercentage.toFixed(0)}%</div>
                </div>
            </td>
        `;
        tbody.appendChild(row);
    });

    table.appendChild(tbody);
    modalBody.appendChild(table);
}
