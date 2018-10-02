from django.db import models
from django.db.models import Func
from django.utils.functional import cached_property
from django.utils.translation import ugettext_lazy as _

from filer.models import File


class FileGrouper(models.Model):
    class Meta:
        verbose_name = _('filer grouper')
        verbose_name_plural = _('filer groupers')

    def __str__(self):
        return self.name

    @cached_property
    def published_file(self):
        return self.files.first()

    @cached_property
    def name(self):
        return 'File grouper {} ({})'.format(
            self.pk,
            getattr(
                self.published_file,
                'label',
                'not published',
            )
        )


grouper_fk_field = models.ForeignKey(
    to=FileGrouper,
    name='grouper',
    on_delete=models.CASCADE,
    related_name='files',
    null=True,
)
grouper_fk_field.contribute_to_class(File, 'grouper')


def get_files_distinct_grouper_queryset():
    from .cms_config import file_versionable
    return file_versionable().distinct_groupers()


class NullIfEmptyStr(Func):
    template = "NULLIF(%(expressions)s, '')"


def copy_file(file_object):
    pass
