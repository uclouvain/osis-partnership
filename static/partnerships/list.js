function renderLink (text, css_class) {
    return function (data, type, row) {
        var content = '<a href="' + row.url + '"';
        if (css_class) {
            content += ' class="' + css_class + '"';
        }
        return content + '>' + (text === 'data' ? data : text) + '</a>';
    }
}

function renderBool (data) {
    return '<i class="fas ' + (data ? 'fa-check text-success' : 'fa-times text-danger') + '"></i>';
}

function initDataTable (storageKey, url, columnDefs, extra) {
    initializeDataTable('filter-form', 'result-list', 'partnershipIds', null, null, url, columnDefs, $.extend({}, {
        // Pagination
        paging: true,
        lengthChange: false,
        pagingType: 'full_numbers',
        lengthMenu: [20],
        info: true,
        dom: '<"row"<"float-end text-end"i>>' +
          '<"row"<"col-12"tr>>' +
          '<"float-start"p>',
        ajax: {
            data: function (d) {
                var querystring = getDataAjaxTable('filter-form', $('#result-list'), d);
                // Calculate the current page number
                querystring['page'] = (d.start / d.length) + 1;
                return querystring;
            },
            dataFilter: function (data) {
                var json = jQuery.parseJSON(data);
                json.recordsTotal = json.total;
                json.recordsFiltered = json.total;
                json.data = json.object_list;

                return JSON.stringify(json); // return JSON string
            }
        },
        autoWidth: false,
        infoCallback: function (settings, start, end, max) {
            var fmts = ngettext('%(count)s_result_count', '%(count)s_results_count', max);
            return interpolate(fmts, { count: max }, true);
        },
        language: {
            paginate: {
                first: '<i class="fas fa-step-backward"></i>',
                previous: '<i class="fas fa-arrow-left"></i>',
                next: '<i class="fas fa-arrow-right"></i>',
                last: '<i class="fas fa-step-forward"></i>'
            }
        }
    }, extra));
}

(function ($) {
    // Handle fields relying on certain types
    var type = $('#id_partnership_type')
    function collapseMobilityFields () {
        var value = type.val();
        $('.only-mobility').toggle(value === 'MOBILITY');
        if (value !== 'MOBILITY') {
            $('.only-mobility select').val('')
        }
        $('#project-fields').toggle(value === 'PROJECT');
        if (value !== 'PROJECT') {
            $('#project-fields select').val('')
        }
        $('#subtype-field').toggle(!['', 'MOBILITY', 'PROJECT'].includes(value));
        if (['', 'MOBILITY', 'PROJECT'].includes(value)) {
            $('#subtype-field select').val('')
        }
        $('.except-general-project').toggle(!['', 'GENERAL', 'PROJECT'].includes(value));
        if (['', 'GENERAL', 'PROJECT'].includes(value)) {
            $('.except-general-project select').val('')
        }
        $('.special-dates-filter').toggle(['', 'GENERAL', 'PROJECT'].includes(value));
        if (!['', 'GENERAL', 'PROJECT'].includes(value)) {
            $('.special-dates-filter select').val('')
        }
        $('.agreements-dates-filter').toggle(value !== 'MOBILITY');
        if (value === 'MOBILITY') {
            $('.agreements-dates-filter select').val('')
        }
    }
    collapseMobilityFields();
    type.on('change', collapseMobilityFields);

    var $form = $('#filter-form');
    function updateExportButtons () {
        $('#results .btn-export').each(function() {
            $(this).attr('href', $(this).data('base-href') + '?' + $form.serialize());
        });

        // Replace url to facilitate history
        var state = $form.serializeArray().filter(function (o) {return o.value !== ""});
        var newUrl = location.href.replace(location.search, '') + '?' + $.param(state);
        history.replaceState(state, "", newUrl);
    }

    $form.on('submit', function () {
        // Validate some fields
        if ($('#id_partnership_date_type').val()) {
            // Dates must be set
            var from = moment($('#id_partnership_date_from').val(), "DD/MM/YYYY");
            var to = moment($('#id_partnership_date_to').val(), "DD/MM/YYYY");
            if (!from.isValid()) {
                alert("Veuillez compléter les dates de recherche");
                return false;
            } else if (to.isValid() && from > to) {
                alert("Les dates de recherche doivent se suivre");
                return false;
            }
        }

        $('#result-list').DataTable().ajax.reload();
        updateExportButtons();
        return false;
    });

    // Update export buttons when changing history
    updateExportButtons();

    // Use click handler and not reset event to be able to prevent default
    $form.on('reset', function (e) {
        // Manually reset autocomplete
        $('[data-autocomplete-light-function=select2]').val('').trigger('change');

        // Manually reset fields, because we don't want to reset hidden fields
        $form.find(':input').not(':button, :submit, :reset, [type=hidden], [type=checkbox]')
            .val('');
        $form.find(':input:checked').prop('checked', false);
        // Manually reset select
        $form.find('select').not('[data-autocomplete-light-function=select2]').each(function () {
            this.selectedIndex = 0;
        }).trigger('change');

        $('#id_partnership_date_from').val(moment().format('DD/MM/YYYY'))
        $('#id_partnership_date_to').val(moment().format('DD/MM/YYYY'))

        // Prevent browser default reset
        e.preventDefault();
        e.stopPropagation();

        // Update list
        $form.trigger('submit');
    });
})(jQuery);
