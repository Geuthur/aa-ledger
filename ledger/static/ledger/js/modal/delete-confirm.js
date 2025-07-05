$(document).ready(() => {
    /* global ledgersettings */
    const modalRequestApprove = $('#ledger-delete-confirm');
    const modalErrorMessage = $('#modal-error-message');

    // Approve Request Modal
    modalRequestApprove.on('show.bs.modal', (event) => {
        const button = $(event.relatedTarget);
        const url = button.data('action');

        // Extract the title from the button
        const modalTitle = button.data('title');
        const modalTitleDiv = modalRequestApprove.find('#modal-title');
        modalTitleDiv.html(modalTitle);

        // Extract the text from the button
        const modalText = button.data('text');
        const modalDiv = modalRequestApprove.find('#modal-request-text');
        modalDiv.html(modalText);

        $('#modal-button-confirm-delete-request').on('click', () => {
            const form = modalRequestApprove.find('form');
            const csrfMiddlewareToken = form.find('input[name="csrfmiddlewaretoken"]').val();

            // Remove any existing error messages
            form.find('.alert-danger').remove();

            const posting = $.post(
                url,
                {
                    csrfmiddlewaretoken: csrfMiddlewareToken
                }
            );

            posting.done(() => {
                modalRequestApprove.modal('hide');
                window.location.reload();
            }).fail((xhr, _, __) => {
                const response = JSON.parse(xhr.responseText);
                modalErrorMessage.text(response.message).removeClass('d-none'); // Show the error message
                modalErrorMessage.addClass('l-shake'); // Add the shake class

                // Remove the shake class after 2 seconds
                setTimeout(() => {
                    modalErrorMessage.removeClass('l-shake');
                }, 2000);
            });
        });
    }).on('hide.bs.modal', () => {
        modalRequestApprove.find('.alert-danger').remove();
        $('#modal-button-confirm-delete-request').unbind('click');
        modalErrorMessage.addClass('d-none');
        modalErrorMessage.val('');
    });
});
