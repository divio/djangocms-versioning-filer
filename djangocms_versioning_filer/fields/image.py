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

    def clean(self, value):
        Image = load_model(filer.settings.FILER_IMAGE_MODEL)
        self.queryset = self.queryset.filter(files=File._base_manager.instance_of(Image))
        return super().clean(value)


class ImageGrouperField(FileGrouperField):
    default_form_class = AdminImageGrouperFormField
