from django.db import models
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _

from djangocms_picture.models import AbstractPicture

from djangocms_versioning_filer.fields import ImageGrouperField


class VersionedPicture(AbstractPicture):
    file_grouper = ImageGrouperField(
        verbose_name=_('File grouper'),
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name='+',
    )

    @cached_property
    def picture(self):
        if self.file_grouper_id:
            return self.file_grouper.file
