$(document).ready(() => {
    /* global SkillFarmAjax */
    const modalRequestApprove = $('#ledger-planetary-confirm');



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

        // Set the character_id in the hidden input field
        const characterId = button.data('character-id');
        modalRequestApprove.find('input[name="character_id"]').val(characterId);

        // Set the planet_id in the hidden input field
        const planetId = button.data('planet-id');
        modalRequestApprove.find('input[name="planet_id"]').val(planetId);

        $('#modal-button-confirm-confirm-request').on('click', () => {
            const form = modalRequestApprove.find('form');
            const csrfMiddlewareToken = form.find('input[name="csrfmiddlewaretoken"]').val();

            // Remove any existing error messages
            form.find('.alert-danger').remove();

            const posting = $.post(
                url,
                {
                    character_id: characterId,
                    planet_id: planetId,
                    csrfmiddlewaretoken: csrfMiddlewareToken
                }
            );

            posting.done(() => {
                modalRequestApprove.modal('hide');
                location.reload();
            }).fail((xhr, _, __) => {
                const response = JSON.parse(xhr.responseText);
                const errorMessage = $('<div class="alert alert-danger"></div>').text(response.message);
                form.append(errorMessage);
            });
        });
    }).on('hide.bs.modal', () => {
        modalRequestApprove.find('.alert-danger').remove();
        $('#modal-button-confirm-confirm-request').unbind('click');
    });
});
