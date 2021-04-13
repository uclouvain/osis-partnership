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

    var $projectAcronym = $('#project-acronym');
    var $partnerEntities = $('#id_partner_entities');
    $partnerEntities.on('change', function () {
        var multiplePartners = $partnerEntities.val() && $partnerEntities.val().length > 1;
        $projectAcronym.toggle(!!(multiplePartners || $projectAcronym.val()))
    }).trigger('change');

    $('input[name="year-entity"]').val($('select[name="ucl_entity"]').val());
    document.querySelector('select[name="ucl_entity"]').onchange = function() {
        $('input[name="year-entity"]').val($(this).val());
        $('select[name="year-entities"]').val([]).trigger('change');
        $('select[name="year-offers"]').val([]).trigger('change');
    };
})(jQuery);
