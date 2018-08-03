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

    $('#filter-form #id_tags').select2({
        language: "fr",
        width: "100%",
        placeholder: "Tags"
    });
})(jQuery);