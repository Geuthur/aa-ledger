function setupModal(modalId, ajaxDataAttr, contentId, loaderId) {
    $(modalId).on('show.bs.modal', function (event) {
        const button = $(event.relatedTarget);
        let ajaxUrl = button.data(ajaxDataAttr);
        const modal = $(this);

        // reactive loader
        modal.find(contentId).hide();
        modal.find(loaderId).show();

        modal.find(contentId).load(
            ajaxUrl,
            function(response, status, xhr) {
                modal.find(loaderId).hide();
                modal.find(contentId).show();

                if ([403, 404, 500].includes(xhr.status)) {
                    modal.find(contentId).html(response);
                    modal.find('.modal-title').html('Error');
                    return;
                }

                // Extract and set the modal title
                const title = modal.find(contentId).find('#modal-title').html();
                modal.find('.modal-title').html(title);
                modal.find('.modal-title').removeClass('d-none');
                modal.find(contentId).find('#modal-title').hide();
            }
        );
    }).on('hidden.bs.modal', function () {
        // Clear the modal content when it is hidden
        $(this).find(contentId).html('');
    });
}

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
