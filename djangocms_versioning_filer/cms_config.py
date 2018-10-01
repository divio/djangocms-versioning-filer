from django.apps import apps

from cms.app_base import CMSAppConfig

from djangocms_versioning.datastructures import VersionableItem
import filer.settings

from .models import copy_file


def versioning_filer_models_config(models):
    for model in models:
        # clear field cache, so that models inheriting from File
        # notice the new File.grouper field
        model._meta._get_fields_cache = {}
        yield VersionableItem(
            content_model=model,
            grouper_field_name='grouper',
            copy_function=copy_file,
            grouper_selector_option_label=lambda obj, language: obj.name,
        )


class FilerVersioningCMSConfig(CMSAppConfig):
    djangocms_versioning_enabled = True
    versioning = list(versioning_filer_models_config(
        apps.get_model(model) for model in filer.settings.FILER_FILE_MODELS
    ))
