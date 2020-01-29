from django.test import TestCase
from django.apps import apps


class ExterrnalIdNotEditableTest(TestCase):

    def setUp(self):
        app_name = 'partnership'
        models_in_partnership_app = [apps.get_model(app_name, model_name) for model_name in apps.all_models[app_name]]
        self.model_containing_external_id = [
            model_class for model_class in models_in_partnership_app
            if 'external_id' in [f.name for f in model_class._meta.fields]
        ]

    def test_external_id_is_not_updatable(self):
        for model_class in self.model_containing_external_id:
            for f in model_class._meta.fields:
                if f.name == 'external_id':
                    error_msg = "field 'external_id' can't be editable (model = {})".format(model_class)
                    self.assertFalse(f.editable, error_msg)
