(function ($) {

    $(document).on('change', '.resetting', function(event) {
        $($(this).attr("data-reset")).each(function(index, elem){
            $(elem).val(null).trigger('change');
        });
    });

})(jQuery);
