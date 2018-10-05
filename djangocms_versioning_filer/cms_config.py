from functools import lru_cache

from django.apps import apps

from cms.app_base import CMSAppConfig

import filer.settings
from djangocms_versioning.datastructures import (
    PolymorphicVersionableItem,
    VersionableItemAlias,
)

from .models import File, copy_file


def versioning_filer_models_config():
    file_config = PolymorphicVersionableItem(
        content_model=File,
        grouper_field_name='grouper',
        copy_function=copy_file,
        grouper_selector_option_label=lambda obj, language: obj.name,
    )
    yield file_config
    for model_name in filer.settings.FILER_FILE_MODELS:
        model = apps.get_model(model_name)
        if model == File:
            continue
        model._meta._get_fields_cache = {}
        yield VersionableItemAlias(content_model=model, to=file_config)


@lru_cache(maxsize=1)
def file_versionable():
    versioning_extension = apps.get_app_config('djangocms_versioning').cms_extension
    return versioning_extension.versionables_by_content[File]


class FilerVersioningCMSConfig(CMSAppConfig):
    djangocms_versioning_enabled = True
    versioning = list(versioning_filer_models_config())
