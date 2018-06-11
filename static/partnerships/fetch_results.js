(function ($) {
    // Pagination/ordering in AJAX
    $(document).on('click', 'a.ajax-results', function(event) {
        event.preventDefault();
        event.stopPropagation();

        var url = $(this).attr('href');
        $.get(url, function(data) {
            $('#results').html(data);
        });
    });

    // Filter form submit in AJAX
    $(document).on('submit', 'form#filter-form', function(event) {
        event.preventDefault();
        event.stopPropagation();
        var $form = $(this);

        var url = $form.attr('action') + '?' + $form.serialize();
        $.get(url, function(data) {
            $('#results').html(data);
        });
    });
})(jQuery);