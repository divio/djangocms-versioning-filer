from django.db import models
from django.utils.functional import cached_property
from django.utils.translation import ugettext_lazy as _

from djangocms_picture.models import AbstractPicture

from djangocms_versioning_filer.models import FileGrouper


class OverridenPicture(AbstractPicture):
    file_grouper = models.ForeignKey(
        FileGrouper,
        verbose_name=_('File grouper'),
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name='+',
    )
    picture = None

    @cached_property
    def picture(self):
        return self.file_grouper.file

    class Meta:
        abstract = False
