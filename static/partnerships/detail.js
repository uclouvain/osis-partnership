(function ($) {
    // Pagination/ordering in AJAX
    var $modal = $('#modal-media-create');
    var $modal_body = $('#modal-media-create .modal-body');

    $(document).on('click', '#add-media', function(event) {
        event.preventDefault();
        event.stopPropagation();

        var url = $(this).attr('href');

        $modal_body.html('<i class="fa fa-circle-o-notch fa-spin fa-fw fa-5x"></i>');
        $modal.modal('show');

        $.get(url, function(data) {
            $modal_body.html(data);
            $modal_body.find('button[type=submit]').remove();
        }).fail(function(error) {
            console.error(error);
            $modal.modal('hide');
        });
    });

    $(document).on('click', '#modal-media-create .submit', function(event) {
        event.preventDefault();
        event.stopPropagation();

        $modal_body.find('form').submit();
    });
})(jQuery);