from functools import lru_cache

from django.apps import apps
from django.conf import settings

from cms.app_base import CMSAppConfig, CMSAppExtension

import filer.settings
from djangocms_versioning.datastructures import (
    PolymorphicVersionableItem,
    VersionableItemAlias,
)
from filer.models import Image

from .admin import VersioningFilerAdminMixin
from .helpers import get_published_file_path, move_file
from .models import File, copy_file


try:
    apps.get_app_config('djangocms_internalsearch')
    from .internal_search import FilerContentConfig
except (ImportError, LookupError):
    FilerContentConfig = None


def on_file_publish(version):
    file_content = version.content
    file_content._file_data_changed_hint = False
    file_content.file = move_file(file_content, get_published_file_path(file_content))
    file_content.save()

    if type(file_content) is Image:
        file_content.is_public = not file_content.is_public
        file_content.file.delete_thumbnails()
        file_content.is_public = not file_content.is_public


def on_file_unpublish(version):
    file_content = version.content
    file_content._file_data_changed_hint = False
    path = file_content._meta.get_field('file').generate_filename(
        file_content,
        file_content.original_filename,
    )
    file_content.file = move_file(file_content, path)
    file_content.save()

    if type(file_content) is Image:
        file_content.is_public = not file_content.is_public
        file_content.file.delete_thumbnails()
        file_content.is_public = not file_content.is_public


def versioning_filer_models_config():
    file_config = PolymorphicVersionableItem(
        content_model=File,
        grouper_field_name='grouper',
        copy_function=copy_file,
        on_publish=on_file_publish,
        on_unpublish=on_file_unpublish,
        grouper_selector_option_label=lambda obj, language: obj.name,
        content_admin_mixin=VersioningFilerAdminMixin,
    )
    yield file_config
    for model_name in filer.settings.FILER_FILE_MODELS:
        model = apps.get_model(model_name)
        if model == File:
            continue
        model._meta._get_fields_cache = {}
        yield VersionableItemAlias(
            content_model=model,
            to=file_config,
            content_admin_mixin=VersioningFilerAdminMixin,
        )


@lru_cache(maxsize=1)
def file_versionable():
    versioning_extension = apps.get_app_config('djangocms_versioning').cms_extension
    return versioning_extension.versionables_by_content[File]


class FilerVersioningExtension(CMSAppExtension):
    def __init__(self):
        self.file_changelist_actions = []

    def handle_file_changelist_actions(self, file_changelist_actions):
        self.file_changelist_actions.extend(file_changelist_actions)

    def configure_app(self, cms_config):
        if hasattr(cms_config, "djangocms_versioning_filer_file_changelist_actions"):
            self.handle_file_changelist_actions(cms_config.djangocms_versioning_filer_file_changelist_actions)


class FilerVersioningCMSConfig(CMSAppConfig):
    # Versioning config
    djangocms_versioning_enabled = True
    versioning = list(versioning_filer_models_config())
    # Moderation config
    djangocms_moderation_enabled = getattr(settings, 'MODERATION_FILER_ENABLED', True)
    moderated_models = [apps.get_model(model_name) for model_name in filer.settings.FILER_FILE_MODELS]
    # Versioning filer (self) config
    djangocms_versioning_filer_enabled = True
    djangocms_versioning_filer_file_changelist_actions = [
        "djangocms_versioning_filer/admin/action_buttons/manage_versions.html",
        "djangocms_versioning_filer/admin/action_buttons/edit.html",
    ]

    # Internalsearch configuration
    if FilerContentConfig:
        djangocms_internalsearch_enabled = True
        internalsearch_config_list = [
            FilerContentConfig,
        ]
