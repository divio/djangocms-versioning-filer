from django.db.utils import OperationalError

import filer
from filer.models import File
from filer.utils.loader import load_model

from .file import (
    AdminFileGrouperFormField,
    AdminFileGrouperWidget,
    FileGrouperField,
)


class AdminImageGrouperWidget(AdminFileGrouperWidget):
    pass


class AdminImageGrouperFormField(AdminFileGrouperFormField):
    widget = AdminImageGrouperWidget

    def __init__(self, rel, queryset, *args, **kwargs):
        Image = load_model(filer.settings.FILER_IMAGE_MODEL)
        try:
            queryset = queryset.filter(files=File._base_manager.instance_of(Image))
        except OperationalError:
            # Error occurs before running migration, and there is no
            # content_type table in db
            pass
        super().__init__(rel, queryset, *args, **kwargs)


class ImageGrouperField(FileGrouperField):
    default_form_class = AdminImageGrouperFormField
