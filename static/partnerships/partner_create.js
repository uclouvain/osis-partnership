(function ($) {
    // Similar partners in AJAX
    var $similar = $('#similar-partners');
    var xhr = null;
    $(document).on('keyup', '#id_partner-name', function(event) {
        if (xhr !== null) {
            xhr.abort();
        }
        if (event.key.length !== 1) {
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