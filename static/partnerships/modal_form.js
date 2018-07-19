(function ($) {
    // Pagination/ordering in AJAX

    $(document).on('click', '.modal-link', function(event) {
        event.preventDefault();
        event.stopPropagation();

        var $modal = $('#' + $(this).data('modal'));
        var $modal_body = $modal.find('.modal-body');
        var $modal_submit = $modal.find('form *[type=submit]');
        var url = $(this).attr('href');
        var submit = $(this).data('modal-submit');
        var title = $(this).data('modal-title');
        var isDanger = $(this).data('modal-danger') !== undefined;

        $modal.find('form').attr('action', url);
        $modal.find('.modal-title').text(title);
        $modal_body.html('<i class="fa fa-circle-o-notch fa-spin fa-fw fa-5x"></i>');
        $modal_submit.text(submit);
        if (isDanger) {
            $modal_submit.removeClass('btn-primary').addClass('btn-danger');
        } else {
            $modal_submit.removeClass('btn-danger').addClass('btn-primary');
        }
        $modal.modal('show');

        $.get(url, function(data) {
            $modal_body.html(data);
            $modal_body.find('.button-row').remove();
            $modal_body.find('button[type=submit]').remove();
        }).fail(function(error) {
            console.error(error);
            $modal.modal('hide');
        });
    });
})(jQuery);