function renderLink (text, css_class) {
    return function (data, type, row) {
        let content = '<a href="' + row.url + '"';
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
    initializeDataTable('filter-form', 'result-list', 'partnershipIds', null, null, url, columnDefs, {
        // Pagination
        paging: true,
        lengthChange: false,
        pagingType: 'full_numbers',
        lengthMenu: [20],
        info: true,
        dom: '<"row"<"pull-right"i>>' +
          '<"row"<"col-sm-12"tr>>' +
          '<"pull-left"p>',
        ajax: {
            data: function (d) {
                let querystring = getDataAjaxTable('filter-form', $('#result-list'), d);
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
            },
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
                last: '<i class="fas fa-step-forward"></i>',
            },
        },
    });
}

(function ($) {
    // Needed for select 2
    $('select').parents('form').on('reset', function (event) {
        event.stopPropagation();
        event.preventDefault();
        $(this).find('input,select').val('').change();
    });

    $('[data-toggle="tooltip"]').tooltip();

    let $form = $('#filter-form');

    function updateExportButton () {
        let $export = $('#results .btn-export');
        $export.attr('href',
          $export.data('base-href') + '?' + $form.serialize(),
        );
    }

    $form.on('submit', function () {
        $('#result-list').DataTable().ajax.reload();
        updateExportButton();
        return false;
    }).on('reset', function () {
        yl.jQuery('[data-autocomplete-light-function=select2]').val('').trigger('change');
        updateExportButton();
        $('#result-list').DataTable().ajax.reload();
    })
})(jQuery);
