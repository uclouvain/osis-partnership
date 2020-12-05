(function ($) {

    var check_show_sm_details = function() {
        if ($('#partnership-form-sm-inputs input:checked').length !== 0) {
            $('#partnership-form-sm-details').collapse('show');
        } else {
            $('#partnership-form-sm-details').collapse('hide');
        }
    };

    $(document).on('change', '#partnership-form-sm-inputs', function(event) {
        check_show_sm_details();
    });

    $('#id_partner').on('select2:select', function (e) {
        var data = e.params.data;
        $('#partner-pic-code').text(data.pic_code || '');
        $('#partner-erasmus-code').text(data.erasmus_code || '');
        var $partnerEntityLink = $('#partner-entity-create-link');

        $partnerEntityLink.attr('href', $partnerEntityLink.attr('data-href').replace('0', data.id)).removeClass('hidden');
    });

    $('input[name="year-entity"]').val($('select[name="ucl_entity"]').val());
    document.querySelector('select[name="ucl_entity"]').onchange = function() {
        $('input[name="year-entity"]').val($(this).val());
        $('select[name="year-entities"]').val([]).trigger('change');
        $('select[name="year-offers"]').val([]).trigger('change');
    };
})(jQuery);
