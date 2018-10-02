import filer
from filer.models import File


def images_with_missing_data_files(self):
    return File._original_manager.filter(has_all_mandatory_data=False)
filer.models.virtualitems.ImagesWithMissingData.files = property(images_with_missing_data_files)   # noqa: E305


def unsorted_images_files(self):
    return File._original_manager.filter(folder__isnull=True)
filer.models.virtualitems.UnsortedImages.files = property(unsorted_images_files)   # noqa: E305

filer.models.File._meta.base_manager_name = '_original_manager'
