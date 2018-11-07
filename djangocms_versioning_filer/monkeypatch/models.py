from django.utils.translation import ugettext_lazy as _

import filer
from djangocms_versioning.exceptions import ConditionFailed
from djangocms_versioning.models import Version

from ..helpers import check_file_exists_in_folder
from ..models import get_files_distinct_grouper_queryset


def images_with_missing_data_files(self):
    return get_files_distinct_grouper_queryset().filter(has_all_mandatory_data=False)
filer.models.virtualitems.ImagesWithMissingData.files = property(images_with_missing_data_files)   # noqa: E305


def unsorted_images_files(self):
    return get_files_distinct_grouper_queryset().filter(folder__isnull=True)
filer.models.virtualitems.UnsortedImages.files = property(unsorted_images_files)   # noqa: E305

filer.models.File._meta.base_manager_name = '_original_manager'


def is_file_content_valid_for_revert(version, user):
    content = version.content
    if isinstance(content, filer.models.File) and check_file_exists_in_folder(content):
        raise ConditionFailed(
            _('File with name "{}" already exists in "{}" folder').format(
                content.label, content.folder,
            )
        )


def is_file_content_valid_for_discard(version, user):
    content = version.content
    if isinstance(content, filer.models.File):
        try:
            latest_version = Version.objects.filter_by_grouper(content.grouper).exclude(pk=version.pk).latest('created')
        except Version.DoesNotExist:
            return
        if check_file_exists_in_folder(latest_version.content):
            raise ConditionFailed(
                _('File with name "{}" already exists in "{}" folder').format(
                    latest_version.content.label, latest_version.content.folder,
                )
            )


Version.check_revert += [is_file_content_valid_for_revert]
Version.check_discard += [is_file_content_valid_for_discard]
