(function ($) {
    // Similar partners in AJAX
    var $similar = $('#similar-partners');
    var xhr = null;
    $(document).on('keyup', '#id_organization-name', function(event) {
        if (xhr !== null) {
            xhr.abort();
        }
        if (event.key.length !== 1 && event.key !== 'Backspace' && event.key !== 'Delete') {
            return ;
        }
        var val = $(this).val();
        if (val.length < 3) {
            return ;
        }
        var url = $similar.data('url') + '?search=' + val;
        xhr = $.get(url, function(data) {
            $similar.html(data);
        }).fail(function(error) {
            console.error(error);
        });
    });
})(jQuery);
