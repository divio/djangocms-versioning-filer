import os
from functools import lru_cache

from django.apps import apps
from django.conf import settings
from django.core.files.base import ContentFile

from cms.app_base import CMSAppConfig

import filer.settings
from djangocms_versioning.datastructures import (
    PolymorphicVersionableItem,
    VersionableItemAlias,
)

from .models import File, copy_file


def _move_file(file_content, destination):
    storage = file_content.file.storage
    src_file = storage.open(file_content.file.name)
    src_file.open()
    new_file = storage.save(destination, ContentFile(src_file.read()))
    storage.delete(file_content.file.name)
    return new_file


def on_file_publish(version):
    file_content = version.content
    if file_content.folder:
        path = file_content.folder.get_ancestors(
            include_self=True,
        ).values_list('name', flat=True)
    else:
        path = []
    path = list(path) + [file_content.original_filename]
    file_content._file_data_changed_hint = False
    file_content.file = _move_file(file_content, os.path.join(*path))
    file_content.save()


def on_file_unpublish(version):
    file_content = version.content
    file_content._file_data_changed_hint = False
    path = file_content._meta.get_field('file').generate_filename(
        file_content,
        file_content.original_filename,
    )
    file_content.file = _move_file(file_content, path)
    file_content.save()


def versioning_filer_models_config():
    file_config = PolymorphicVersionableItem(
        content_model=File,
        grouper_field_name='grouper',
        copy_function=copy_file,
        on_publish=on_file_publish,
        on_unpublish=on_file_unpublish,
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
    djangocms_moderation_enabled = getattr(settings, 'MODERATION_FILER_ENABLED', True)
    moderated_models = [apps.get_model(model_name) for model_name in filer.settings.FILER_FILE_MODELS]
