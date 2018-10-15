from .file import (
    AdminFileGrouperFormField,
    AdminFileGrouperWidget,
    FileGrouperField,
)


class AdminImageGrouperWidget(AdminFileGrouperWidget):
    pass


class AdminImageGrouperFormField(AdminFileGrouperFormField):
    widget = AdminImageGrouperWidget


class ImageGrouperField(FileGrouperField):
    default_form_class = AdminImageGrouperFormField
    # default_model_class =
    # TODO create ImageGrouper proxy
