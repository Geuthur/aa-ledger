var images = [];
var currentIndex = 0;

$('.zoom').on('click', function() {
    images = $('.zoom').map(function() {
        return {
            src: $(this).data('src'),
            alt: $(this).attr('alt')
        };
    }).get();

    currentIndex = $(this).index('.zoom');
    updateModalImage(currentIndex);
});

$('#nextImage').on('click', function() {
    currentIndex = (currentIndex + 1) % images.length;
    updateModalImage(currentIndex);
});

$('#prevImage').on('click', function() {
    currentIndex = (currentIndex - 1 + images.length) % images.length;
    updateModalImage(currentIndex);
});

function updateModalImage(index) {
    $('#modalImage').attr('src', images[index].src);
    $('#imageText').html(images[index].alt);
}
