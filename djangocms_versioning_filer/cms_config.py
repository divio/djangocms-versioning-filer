from cms.app_base import CMSAppConfig

from djangocms_versioning.datastructures import VersionableItem
from filer.models import File

from .models import copy_file


class FilerVersioningCMSConfig(CMSAppConfig):
    djangocms_versioning_enabled = True
    versioning = [
        VersionableItem(
            content_model=File,
            grouper_field_name='grouper',
            copy_function=copy_file,
            grouper_selector_option_label=lambda obj: obj.name,
        ),
    ]
