from datetime import datetime

from django.conf import settings
from django.db import models
from django.db.models import Func
from django.utils import timezone
from django.utils.functional import cached_property
from django.utils.translation import ugettext_lazy as _

from filer.models import File

from .constants import PUBLIC_RELATIVE_PATH


class FileGrouper(models.Model):

    canonical_created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    canonical_file_id = models.CharField(null=True, max_length=255)

    class Meta:
        verbose_name = _("filer grouper")
        verbose_name_plural = _("filer groupers")

    def __str__(self):
        return self.name

    @cached_property
    def file(self):
        return self.files.first()

    @property
    def file_relative_url(self):
        """
        Remove the base url to make the file url relative to the current site
        """
        url = self.file.file.url
        base_url = self.file.file.storage.base_url
        return url.replace(base_url, PUBLIC_RELATIVE_PATH)

    @property
    def canonical_time(self):
        if settings.USE_TZ:
            return int((self.canonical_created_at - datetime(1970, 1, 1, 1, tzinfo=timezone.utc)).total_seconds())
        else:
            return int((self.canonical_created_at - datetime(1970, 1, 1, 1)).total_seconds())

    @cached_property
    def name(self):
        return "File grouper {} ({})".format(
            self.pk, getattr(self.file, "label", "not published")
        )

    def get_absolute_url(self):
        from djangocms_versioning.helpers import version_list_url_for_grouper

        return version_list_url_for_grouper(self)


grouper_fk_field = models.ForeignKey(
    to=FileGrouper,
    name="grouper",
    on_delete=models.CASCADE,
    related_name="files",
    null=True,
)
grouper_fk_field.contribute_to_class(File, "grouper")


def get_files_distinct_grouper_queryset():
    from .cms_config import file_versionable

    return file_versionable().distinct_groupers()


class NullIfEmptyStr(Func):
    template = "NULLIF(%(expressions)s, '')"
    arity = 1


def copy_file(original_file):
    model = original_file.__class__
    file_fields = {
        field.name: getattr(original_file, field.name)
        for field in model._meta.fields
        if field.name not in ("id", "file_ptr", "file")
    }
    file_fields["file"] = original_file._copy_file(
        model._meta.get_field("file").generate_filename(
            original_file, original_file.original_filename
        )
    )
    new_file = model.objects.create(**file_fields)
    new_file.__class__ = File
    return new_file
