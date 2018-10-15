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
        self.file_model = load_model(filer.settings.FILER_IMAGE_MODEL)
        super().__init__(rel, queryset, *args, **kwargs)

    def _get_queryset(self):
        try:
            return self._queryset.filter(files=File._base_manager.instance_of(self.file_model))
        except OperationalError:
            # Error occurs before running migration, and there is no
            # content_type table in db
            return self._queryset

    def _set_queryset(self, queryset):
        self._queryset = queryset
        self.widget.choices = self.choices

    queryset = property(_get_queryset, _set_queryset)


class ImageGrouperField(FileGrouperField):
    default_form_class = AdminImageGrouperFormField
