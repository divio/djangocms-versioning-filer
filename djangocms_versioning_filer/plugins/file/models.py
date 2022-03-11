from django.db import models
from django.utils.functional import cached_property
from django.utils.translation import gettext, gettext_lazy as _

from cms.models import CMSPlugin

from djangocms_attributes_field.fields import AttributesField
from djangocms_file.models import LINK_TARGET, Folder, get_templates

from djangocms_versioning_filer.fields import FileGrouperField
from djangocms_versioning_filer.models import (
    get_files_distinct_grouper_queryset,
)


class VersionedFile(CMSPlugin):
    search_fields = ('name',)

    template = models.CharField(
        verbose_name=_('Template'),
        choices=get_templates(),
        default=get_templates()[0][0],
        max_length=255,
    )
    file_grouper = FileGrouperField(
        verbose_name=_('File grouper'),
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name='+',
    )
    file_name = models.CharField(
        verbose_name=_('Name'),
        blank=True,
        max_length=255,
        help_text=_('Overrides the default file name with the given value.'),
    )
    link_target = models.CharField(
        verbose_name=_('Link target'),
        choices=LINK_TARGET,
        blank=True,
        max_length=255,
        default='',
    )
    link_title = models.CharField(
        verbose_name=_('Link title'),
        blank=True,
        max_length=255,
    )
    show_file_size = models.BooleanField(
        verbose_name=_('Show file size'),
        blank=True,
        default=False,
        help_text=_('Appends the file size at the end of the name.'),
    )
    attributes = AttributesField(
        verbose_name=_('Attributes'),
        blank=True,
        excluded_keys=['href', 'title', 'target'],
    )

    # Add an app namespace to related_name to avoid field name clashes
    # with any other plugins that have a field with the same name as the
    # lowercase of the class name of this model.
    # https://github.com/divio/django-cms/issues/5030
    cmsplugin_ptr = models.OneToOneField(
        CMSPlugin,
        related_name='%(app_label)s_%(class)s',
        on_delete=models.CASCADE,
        parent_link=True,
    )

    def __str__(self):
        if self.file_src and self.file_src.label:
            return self.file_src.label
        return str(self.pk)

    @cached_property
    def file_src(self):
        if self.file_grouper_id:
            return self.file_grouper.file

    def get_short_description(self):
        if self.file_src and self.file_name:
            return self.file_name
        if self.file_src and self.file_src.label:
            return self.file_src.label
        return gettext('<file is missing>')

    def copy_relations(self, oldinstance):
        # Because we have a ForeignKey, it's required to copy over
        # the reference from the instance to the new plugin.
        self.file_src = oldinstance.file_src


def folder_model_get_files(self):
    folder_files = []
    if self.folder_src:
        for _file in get_files_distinct_grouper_queryset().filter(folder=self.folder_src):
            folder_files.append(_file)
    return folder_files
Folder.get_files = folder_model_get_files  # noqa: E305
