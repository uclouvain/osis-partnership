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
        $('#partner-pic-code').text("");
        $('#partner-erasmus-code').text("");
        if (data.pic_code !== null) {
            $('#partner-pic-code').text(data.pic_code);
        }
        if (data.erasmus_code !== null) {
            $('#partner-erasmus-code').text(data.erasmus_code);
        }

        var $partnerEntityLink = $('#partner-entity-create-link');

        $partnerEntityLink.attr('href', $partnerEntityLink.attr('data-href').replace('0', data.id)).removeClass('hidden');
    });

})(jQuery);
