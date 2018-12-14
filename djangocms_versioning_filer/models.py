from django.core.urlresolvers import reverse
from django.db import models
from django.db.models import Func
from django.utils.functional import cached_property
from django.utils.html import format_html
from django.utils.translation import ugettext_lazy as _

from cms.utils.helpers import is_editable_model

from filer.models import File


class FileGrouper(models.Model):
    class Meta:
        verbose_name = _('filer grouper')
        verbose_name_plural = _('filer groupers')

    def __str__(self):
        return self.name

    @cached_property
    def file(self):
        return self.files.first()

    @cached_property
    def name(self):
        return 'File grouper {} ({})'.format(
            self.pk,
            getattr(
                self.file,
                'label',
                'not published',
            )
        )

    def get_absolute_url(self):
        from djangocms_versioning.helpers import version_list_url_for_grouper
        return version_list_url_for_grouper(self)


def get_preview_url(self):
    # If the object is editable the preview view should be used.
    if is_editable_model(self.__class__):
        url = get_object_preview_url(self)
    # Or else, the standard change view should be used
    else:
        url = reverse('admin:{app}_{model}_change'.format(
            app=self._meta.app_label,
            model=self._meta.model_name,
        ), args=[self.pk])

    return url


File.get_preview_url = get_preview_url


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
    arity = 1


def copy_file(original_file):
    model = original_file.__class__
    file_fields = {
        field.name: getattr(original_file, field.name)
        for field in model._meta.fields
        if field.name not in ('id', 'file_ptr', 'file')
    }
    file_fields['file'] = original_file._copy_file(
        model._meta.get_field('file').generate_filename(
            original_file,
            original_file.original_filename,
        ),
    )
    new_file = model.objects.create(**file_fields)
    new_file.__class__ = File
    return new_file
