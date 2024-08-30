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

    fetch(url)
        .then(response => response.json())
        .then(data => {
            const tbody = document.querySelector('#planets-details tbody');
            const characterIds = new Set();

            data.forEach(item => {
                characterIds.add(item.character_id);
                const row = document.createElement('tr');

                // Character
                const characterCell = document.createElement('td');

                // Character Icon
                const characterIconCell = document.createElement('td');
                const characterIcon = document.createElement('img');
                characterIcon.src = `https://images.evetech.net/characters/${item.character_id}/portrait?size=32`; // Adjust the path as needed
                characterIcon.className = 'rounded-circle';
                characterIcon.style.marginRight = '5px';
                characterIcon.style.width = '32px'; // Adjust the size as needed
                characterIcon.style.height = '32px'; // Adjust the size as needed
                characterCell.appendChild(characterIcon);

                // Character Text
                const characterText = document.createTextNode(item.character_name);
                characterCell.appendChild(characterText);

                row.appendChild(characterCell);

                // Planet Type
                const planetTypeCell = document.createElement('td');

                // Planet Icon
                const planetIcon = document.createElement('img');
                planetIcon.src = `https://images.evetech.net/types/${item.planet_type_id}/icon?size=32`; // Adjust the path as needed
                planetIcon.className = 'rounded-circle';
                planetIcon.style.marginRight = '5px';
                planetIcon.style.width = '24px'; // Adjust the size as needed
                planetIcon.style.height = '24px'; // Adjust the size as needed

                planetTypeCell.appendChild(planetIcon);

                // Planet Text
                const planetText = document.createTextNode(item.planet);
                planetTypeCell.appendChild(planetText);

                // Alarm Icon
                const alarmIcon = document.createElement('i');
                alarmIcon.className = 'fa-solid fa-bullhorn';
                alarmIcon.style.marginLeft = '5px';
                alarmIcon.style.color = 'green';
                alarmIcon.title = alarmActivated;
                if (!item.alarm) {
                    alarmIcon.title = alarmDeactivated;
                    alarmIcon.style.color = 'red';
                }
                planetTypeCell.appendChild(alarmIcon);

                row.appendChild(planetTypeCell);

                // Upgrade Level (assuming you have this data)
                const upgradeLevelCell = document.createElement('td');
                upgradeLevelCell.textContent = item.upgrade_level;
                row.appendChild(upgradeLevelCell);

                // Products
                const productsCell = document.createElement('td');
                productsCell.innerHTML = Object.values(item.products).map(product => {
                    const img = document.createElement('img');
                    img.src = `https://images.evetech.net/types/${product.id}/icon?size=32`;
                    img.title = product.name;
                    return img.outerHTML;
                }).join(' ');
                row.appendChild(productsCell);

                // Extractors
                const extractorsCell = document.createElement('td');
                const extractorsList = document.createElement('ul');
                extractorsList.style.listStyleType = 'none';
                extractorsList.style.padding = 0;
                let extractorCount = Object.values(item.extractors).length;

                if (extractorCount === 0) {
                    extractorsCell.innerHTML = 'No Extractors';
                } else {
                    // Calculate total progress
                    let totalInstallTime = 0;
                    let totalExpiryTime = 0;
                    let currentTime = new Date().getTime();
                    let extractorCount = Object.values(item.extractors).length;

                    Object.values(item.extractors).forEach(extractor => {
                        totalInstallTime += new Date(extractor.install_time).getTime();
                        totalExpiryTime += new Date(extractor.expiry_time).getTime();
                    });

                    // Calculate average times
                    let averageInstallTime = totalInstallTime / extractorCount;
                    let averageExpiryTime = totalExpiryTime / extractorCount;

                    const totalDuration = averageExpiryTime - averageInstallTime;
                    const elapsedDuration = currentTime - averageInstallTime;
                    const progressPercentage = Math.min(Math.max((elapsedDuration / totalDuration) * 100, 0), 100);

                    // Create container for progress bar and info button
                    const progressContainer = document.createElement('div');
                    progressContainer.style.display = 'flex';
                    progressContainer.style.alignItems = 'center';

                    const progressBar = document.createElement('div');
                    progressBar.className = 'progress-outer';
                    progressBar.style.flexGrow = '1';
                    progressBar.style.marginRight = '10px'; // Add some space between the progress bar and the icon
                    progressBar.innerHTML = `
                        <div class="progress">
                            <div class="progress-bar progress-bar-warning progress-bar-striped active" role="progressbar" style="width: ${progressPercentage}%; box-shadow: -1px 10px 10px rgba(240, 173, 78, 0.7);" aria-valuenow="${progressPercentage}" aria-valuemin="0" aria-valuemax="100"></div>
                            <div class="progress-value">${progressPercentage.toFixed(0)}%</div>
                        </div>
                    `;

                    // Info Button
                    const infoButton = document.createElement('button');
                    infoButton.className = 'btn btn-primary btn-sm btn-square';
                    infoButton.style.marginLeft = '5px'; // Add 5px margin to the left
                    infoButton.innerHTML = '<span class="fas fa-info"></span>';
                    infoButton.setAttribute('data-bs-toggle', 'modal');
                    infoButton.setAttribute('data-bs-target', '#extractorInfoModal');
                    infoButton.onclick = function() {
                        const modalTitle = document.querySelector('#extractorInfoModalLabel');
                        modalTitle.textContent = `Extractor Information - ${item.character_name} - ${item.planet}`;

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

                        Object.values(item.extractors).forEach(extractor => {
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
                    };

                    // Append progress bar and info button to the container
                    progressContainer.appendChild(progressBar);
                    progressContainer.appendChild(infoButton);

                    // Append the container to the extractors cell
                    extractorsCell.appendChild(progressContainer);
                }
                row.appendChild(extractorsCell);

                // Status
                const statusCell = document.createElement('td');
                const statusImg = document.createElement('img');
                statusImg.style.width = '24px';
                statusImg.style.height = '24px';
                if (item.expired) {
                    statusImg.src = '/static/ledger/images/red.png';
                    statusImg.title = 'Expired';
                } else {
                    statusImg.src = '/static/ledger/images/green.png';
                    statusImg.title = 'Active';
                }
                statusCell.appendChild(statusImg);
                row.appendChild(statusCell);

                // Actions
                const actionsCell = document.createElement('td');
                actionsCell.className = 'text-end'; // Align the text to the right
                const switchAlarmButton = document.createElement('button');
                switchAlarmButton.textContent = 'Switch Alarm';
                switchAlarmButton.className = 'btn btn-primary';
                const characterId = item.character_id;
                const planetId = item.planet_id;
                const url = switchAlarmUrl(characterId, planetId);
                const csrfToken = planetarySettings.csrfToken;
                const charPk = characterPk;
                var button = '';
                button +=
                    '<form class="d-inline" method="post" action="' + switchAlarmUrl(characterId, planetId) + '" id="switchAlarmForm' + characterId + '_' + planetId + '">' +
                    csrfToken +
                    '<input type="hidden" name="character_pk" value="' + charPk + '">' +
                    '<button type="button" class="btn btn-primary btn-sm btn-square" aria-label="' + switchAlarm + '" title="' + switchAlarm + '" data-bs-toggle="modal" data-bs-target="#confirmModal" data-confirm-text="' + switchAlarmText + '" data-form-id="switchAlarmForm' + characterId + '_' + planetId + '"><span class="fas fa-bullhorn"></span></button></form>';
                actionsCell.innerHTML = button;
                row.appendChild(actionsCell);

                tbody.appendChild(row);
            });

            // Add "Switch All Alarms" button if data exists
            if (data.length > 0) {
                const switchAllAlarmsButton = document.createElement('button');
                switchAllAlarmsButton.textContent = 'Switch All Alarms';
                switchAllAlarmsButton.className = 'btn btn-primary';
                switchAllAlarmsButton.style.marginTop = '10px';

                const switchAllAlarmsForm = document.createElement('form');
                switchAllAlarmsForm.method = 'post';
                switchAllAlarmsForm.action = switchAlarmUrl(characterPk, 0);
                switchAllAlarmsForm.id = 'switchAllAlarmsForm';
                switchAllAlarmsForm.className = 'd-inline';
                switchAllAlarmsForm.innerHTML = csrfToken +
                    '<input type="hidden" name="character_pk" value="' + characterPk + '">' +
                    '<button type="button" class="btn btn-primary btn-sm btn-square" aria-label="' + switchAlarm + '" title="' + switchAlarm + '" data-bs-toggle="modal" data-bs-target="#confirmModal" data-confirm-text="' + switchAlarmText + '" data-form-id="switchAllAlarmsForm">' + switchAllAlarmsButton.textContent + '</button>';

                const tableContainer = document.querySelector('#planets-details').parentElement;
                const switchAllAlarmsContainer = document.createElement('div');
                switchAllAlarmsContainer.className = 'switch-all-alarms-container';
                switchAllAlarmsContainer.appendChild(switchAllAlarmsForm);
                tableContainer.appendChild(switchAllAlarmsContainer);
            }

            // Initialize DataTable with sorting on the expiry column
            $('#planets-details').DataTable({
                'order': [[4, 'desc']], // Adjust the column index if needed
                'pageLength': 25,
                'columnDefs': [
                    { 'orderable': false, 'targets': 'no-sort' }
                ]
            });

            // Initialize Bootstrap tooltips for all elements with a title attribute
            const tooltipTriggerList = [].slice.call(document.querySelectorAll('[title]'));
            const tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
                return new bootstrap.Tooltip(tooltipTriggerEl);
            });
        })
        .catch(error => console.error('Error fetching data:', error));
});
