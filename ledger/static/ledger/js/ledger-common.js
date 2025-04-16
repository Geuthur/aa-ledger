// Gemeinsame Funktionen

$('#modalViewCharacterContainer').on('show.bs.modal', function (event) {
    const button = $(event.relatedTarget);
    const ajax_url = button.data('ajax_url');
    const modal = $(this);

    // reactive loader
    modal.find('#modalViewCharacterContent').hide();
    modal.find('#modalViewCharacterLoader').show();

    $('#modalViewCharacterContent').load(
        ajax_url,
        function(response, status, xhr) {
            modal.find('#modalViewCharacterLoader').hide();
            modal.find('#modalViewCharacterContent').show();

            if (xhr.status === 403) {
                $('#modalViewCharacterContent').html(response);
            }
            // Extract and set the modal title
            const title = $('#modalViewCharacterContent').find('#modal-title').html();
            modal.find('.modal-title').html(title);
            $('#modalViewCharacterContent').find('#modal-title').hide();
        }
    );
});

function updateUrls(entityType, entityPk, selectedYear, selectedMonth, selectedDay, selectedviewMode, singleView) {
    return `/ledger/api/${entityType}/${entityPk}/ledger/date/${selectedYear}-${selectedMonth}-${selectedDay}/view/${selectedviewMode}` +
           (singleView ? `/${singleView}` : '');
}

function getMonthName(monthNumber, translations) {
    const months = translations.months;
    return months[monthNumber - 1]; // Array ist 0-basiert, daher -1
}

function formatAndColor(value) {
    let number = parseFloat(value) || 0;
    number = Math.round(number);
    const formattedNumber = number.toLocaleString();
    const cssClass = number < 0 ? 'text-danger' : (number > 0 ? 'text-success' : '');
    return `<span class="${cssClass}">${formattedNumber}</span> ISK`;
}

function populateDays(selectedYear, selectedMonth, dayDropdown) {
    const daysInMonth = new Date(selectedYear, selectedMonth, 0).getDate();
    dayDropdown.innerHTML = '';
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
    $('[data-tooltip-toggle="ledger-tooltip"]').tooltip({ trigger: 'hover' });
    $('[data-bs-toggle="corp-popover"]').popover({ trigger: 'hover', html: true });
}

function hideLoading() {
    $('#bar-loading, #chart-loading, #loadingIndicator').addClass('d-none');
}

function showLoading() {
    $('#bar-loading, #chart-loading, #loadingIndicator').removeClass('d-none');
}

function hideContainer() {
    $('#lookup, #ratting, #ChartContainer, #rattingBarContainer, #workGaugeContainer').addClass('d-none');
    $('#foot').hide();
}

function handleDropdownClick(event, dropdownType, state, updateCallback) {
    if (event.target && event.target.matches('a.dropdown-item')) {
        const items = event.currentTarget.querySelectorAll('a.dropdown-item');
        items.forEach(item => item.classList.remove('active'));
        event.target.classList.add('active');

        if (dropdownType === 'year') {
            $('#yearDropDownButton').text(event.target.textContent);
            $('#monthDropDownButton').text(state.translations.monthText);
            $('#dayDropDownButton').text(state.translations.dayText);
            state.selectedYear = event.target.dataset.bsYearId;
            state.selectedviewMode = 'year';
        } else if (dropdownType === 'month') {
            $('#monthDropDownButton').text(event.target.textContent);
            $('#dayDropDownButton').text(state.translations.dayText);
            state.selectedMonth = event.target.dataset.bsMonthId;
            state.selectedviewMode = 'month';
        } else if (dropdownType === 'day') {
            $('#dayDropDownButton').text(event.target.textContent);
            state.selectedDay = event.target.textContent;
            state.selectedviewMode = 'day';
        }

        showLoading();
        hideContainer();
        updateCallback();
    }
}
