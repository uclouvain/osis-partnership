(function ($) {
    var showLoader = function() {
        $('#results .loader').delay(200).show(500);
    };

    var hideLoader = function() {
        $('#results .loader').hide(0);
    };

    // Pagination/ordering in AJAX
    $(document).on('click', 'a.ajax-results', function(event) {
        event.preventDefault();
        event.stopPropagation();

        var url = $(this).attr('href');
        showLoader();
        $.get(url, function(data) {
            $('#results').html(data);
            hideLoader();
        }).fail(function(error) {
            console.error(error);
            hideLoader();
        });
    });

    // Filter form submit in AJAX
    $(document).on('submit', 'form#filter-form', function(event) {
        event.preventDefault();
        event.stopPropagation();
        var $form = $(this);

        var url = $form.attr('action') + '?' + $form.serialize();
        showLoader();
        $.get(url, function(data) {
            $('#results').html(data);
            hideLoader();
        }).fail(function(error) {
            console.error(error);
            hideLoader();
        });
    });

    // Needed for select 2
    $('select').parents('form').on('reset', function (event) {
        event.stopPropagation();
        event.preventDefault();
        $(this).find('input,select').val('').change();
    });

    $('[data-toggle="tooltip"]').tooltip();
})(jQuery);