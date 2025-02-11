 document.addEventListener('DOMContentLoaded', function() {
            let uclReference = document.getElementById('id_year-ucl_reference');
            let partnerReferent = document.getElementById('id_year-partner_referent');

            function toggleSelects() {
                if (uclReference.value === 'False') {
                    partnerReferent.parentElement.style.display = '';
                    partnerReferent.disabled = false;
                } else {
                    partnerReferent.parentElement.style.display = 'none';
                    partnerReferent.disabled = true;
                }
            }
            uclReference.addEventListener('change', toggleSelects);

            // Initial call to set the correct state on page load
            toggleSelects();
        });