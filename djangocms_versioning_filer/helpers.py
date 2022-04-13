import collections
import os

from django.apps import apps
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.utils.translation import ugettext as _

import filer
from djangocms_versioning.models import Version
from filer.models import File

from .models import get_files_distinct_grouper_queryset


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


def check_file_label_exists_in_folder(label, folder, exclude_file_pks=None):
    if not isinstance(exclude_file_pks, collections.Iterable):
        exclude_file_pks = []
    files_in_folder = get_files_distinct_grouper_queryset().filter(
        folder=folder,
    ).exclude(pk__in=exclude_file_pks)
    labels_in_folder = [f.label for f in files_in_folder]
    return label in labels_in_folder


def check_file_exists_in_folder(file_obj):
    try:
        latest_version = Version.objects.filter_by_grouper(file_obj.grouper).latest('created')
        exclude_file_pks = [latest_version.object_id]
    except Version.DoesNotExist:
        exclude_file_pks = []

    return check_file_label_exists_in_folder(
        file_obj.label, file_obj.folder, exclude_file_pks=exclude_file_pks,
    )

def filename_exists(request, folder_id=None):
    from filer.models import Folder, File

    FILE_EXISTS = _('File name already exists')

    try:
        # Get folder
        folder = Folder.objects.get(pk=folder_id)
    except Folder.DoesNotExist:
        # if folder not exists then not proceeding further check and return
        return

    if folder:
        if len(request.FILES) == 1:
            # dont check if request is ajax or not, just grab the file
            upload = list(request.FILES.values())[0]
            filename = upload.name
        else:
            # else process the request as usual
            filename = request.GET.get('qqfile', False) or request.GET.get('filename', False) or ''
        if File._original_manager.filter(
            original_filename=filename,
            folder_id=folder_id
        ):
            raise ValidationError(FILE_EXISTS)
    return