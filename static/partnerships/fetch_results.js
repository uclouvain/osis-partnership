(function ($) {
    $(document).ready(function() {
        $(document).on('click', 'a.ajax-results', function(event) {
            event.preventDefault();
            event.stopPropagation();

            var url = $(this).attr('href');
            $.get(url, function(data) {
                $('#results').html(data);
            });
        });
    });
})(jQuery);