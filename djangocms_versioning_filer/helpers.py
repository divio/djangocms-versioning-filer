import os

from django.apps import apps
from django.core.files.base import ContentFile

import filer
from djangocms_versioning.models import Version
from filer.models import File


def create_file_version(file, user):
    # Make sure Version.content_type uses File
    file.__class__ = File
    version = Version.objects.create(content=file, created_by=user)
    file.__class__ = file.get_real_instance_class()
    return version


def move_file(file_content, destination):
    storage = file_content.file.storage
    src_file = storage.open(file_content.file.name)
    src_file.open()
    new_file = storage.save(destination, ContentFile(src_file.read()))
    storage.delete(file_content.file.name)
    return new_file


def get_published_file_path(file_obj):
    if file_obj.folder:
        path = file_obj.folder.get_ancestors(
            include_self=True,
        ).values_list('name', flat=True)
    else:
        path = []
    path = list(path) + [file_obj.original_filename]
    return os.path.join(*path)


def is_moderation_enabled():
    try:
        moderation_config = apps.get_app_config('djangocms_moderation')
        moderated_models = [
            model._meta.label
            for model in moderation_config.cms_extension.moderated_models
        ]
        return all(
            filer_model in moderated_models
            for filer_model in filer.settings.FILER_FILE_MODELS
        )
    except LookupError:
        return False
