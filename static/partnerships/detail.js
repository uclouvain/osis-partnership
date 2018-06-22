(function ($) {
    // Pagination/ordering in AJAX

    $(document).on('click', '.modal-link', function(event) {
        event.preventDefault();
        event.stopPropagation();

        var $modal = $('#' + $(this).attr('data-modal'));
        var $modal_body = $modal.find('.modal-body');
        var url = $(this).attr('href');

        $modal.find('form').attr('action', url);
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
})(jQuery);