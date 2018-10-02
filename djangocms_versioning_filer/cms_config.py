from functools import lru_cache

from django.apps import apps

from cms.app_base import CMSAppConfig

import filer.settings
from djangocms_versioning.datastructures import (
    PolymorphicVersionableItem,
    VersionableItem,
)

from .models import File, copy_file


def versioning_filer_model_config(model, item_class=VersionableItem, **params):
    # clear field cache, so that models inheriting from File
    # notice the new File.grouper field
    model._meta._get_fields_cache = {}
    return item_class(
        content_model=model,
        grouper_field_name='grouper',
        copy_function=copy_file,
        grouper_selector_option_label=lambda obj, language: obj.name,
        **params
    )


def versioning_filer_models_config():
    yield versioning_filer_model_config(File, PolymorphicVersionableItem)
    for model_name in filer.settings.FILER_FILE_MODELS:
        model = apps.get_model(model_name)
        if model == File:
            continue
        yield versioning_filer_model_config(
            model,
            register_version_admin=False,
        )


@lru_cache(maxsize=1)
def file_versionable():
    versioning_extension = apps.get_app_config('djangocms_versioning').cms_extension
    return versioning_extension.versionables_by_content[File]


class FilerVersioningCMSConfig(CMSAppConfig):
    djangocms_versioning_enabled = True
    versioning = list(versioning_filer_models_config())
