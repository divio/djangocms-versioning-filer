from django.core.exceptions import ValidationError
from django.db import models
from django.utils.functional import cached_property
from django.utils.translation import ugettext, ugettext_lazy as _

from cms.models import CMSPlugin

from djangocms_attributes_field.fields import AttributesField
from djangocms_video.models import VideoTrack, get_extensions, get_templates

from djangocms_versioning_filer.fields import (
    FileGrouperField,
    ImageGrouperField,
)


ALLOWED_EXTENSIONS = get_extensions()


class VersionedVideoPlayer(CMSPlugin):
    template = models.CharField(
        verbose_name=_('Template'),
        choices=get_templates(),
        default=get_templates()[0][0],
        max_length=255,
    )
    label = models.CharField(
        verbose_name=_('Label'),
        blank=True,
        max_length=255,
    )
    embed_link = models.CharField(
        verbose_name=_('Embed link'),
        blank=True,
        max_length=255,
        help_text=_(
            'Use this field to embed videos from external services '
            'such as YouTube, Vimeo or others. Leave it blank to upload video '
            'files by adding nested "Source" plugins.'
        ),
    )
    poster_grouper = ImageGrouperField(
        verbose_name=_('Poster'),
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name='+',
    )
    attributes = AttributesField(
        verbose_name=_('Attributes'),
        blank=True,
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
        return self.label or self.embed_link or str(self.pk)

    @cached_property
    def poster(self):
        if self.poster_grouper_id:
            return self.poster_grouper.file

    def copy_relations(self, oldinstance):
        # Because we have a ForeignKey, it's required to copy over
        # the reference from the instance to the new plugin.
        self.poster = oldinstance.poster


class VersionedVideoSource(CMSPlugin):
    file_grouper = FileGrouperField(
        verbose_name=_('File grouper'),
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name='+',
    )
    text_title = models.CharField(
        verbose_name=_('Title'),
        blank=True,
        max_length=255,
    )
    text_description = models.TextField(
        verbose_name=_('Description'),
        blank=True,
    )
    attributes = AttributesField(
        verbose_name=_('Attributes'),
        blank=True,
    )

    def __str__(self):
        if self.source_file and self.source_file.label:
            return self.source_file.label
        return str(self.pk)

    @cached_property
    def source_file(self):
        if self.file_grouper_id:
            return self.file_grouper.file

    def clean(self):
        if self.source_file and self.source_file.extension not in ALLOWED_EXTENSIONS:
            raise ValidationError(
                ugettext('Incorrect file type: {extension}.')
                .format(extension=self.source_file.extension)
            )

    def get_short_description(self):
        if self.source_file and self.source_file.label:
            return self.source_file.label
        return ugettext('<file is missing>')

    def copy_relations(self, oldinstance):
        # Because we have a ForeignKey, it's required to copy over
        # the reference from the instance to the new plugin.
        self.source_file = oldinstance.source_file


class VersionedVideoTrack(CMSPlugin):
    kind = models.CharField(
        verbose_name=_('Kind'),
        choices=VideoTrack.KIND_CHOICES,
        max_length=255,
    )
    file_grouper = FileGrouperField(
        verbose_name=_('File grouper'),
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name='+',
    )
    srclang = models.CharField(
        verbose_name=_('Source language'),
        blank=True,
        max_length=255,
        help_text=_('Examples: "en" or "de" etc.'),
    )
    label = models.CharField(
        verbose_name=_('Label'),
        blank=True,
        max_length=255,
    )
    attributes = AttributesField(
        verbose_name=_('Attributes'),
        blank=True,
    )

    def __str__(self):
        label = self.kind
        if self.srclang:
            label += ' {}'.format(self.srclang)
        return label

    @cached_property
    def src(self):
        if self.file_grouper_id:
            return self.file_grouper.file
