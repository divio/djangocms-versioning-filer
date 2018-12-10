from django.core.exceptions import ValidationError
from django.db import models
from django.utils.functional import cached_property
from django.utils.translation import ugettext, ugettext_lazy as _

from cms.models import CMSPlugin

from djangocms_attributes_field.fields import AttributesField

from djangocms_audio.models import ALLOWED_EXTENSIONS, AudioFolder, AudioTrack
from djangocms_versioning_filer.fields import FileGrouperField
from djangocms_versioning_filer.models import (
    get_files_distinct_grouper_queryset,
)


class VersionedAudioFile(CMSPlugin):
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
        if self.audio_file and self.audio_file.label:
            return self.audio_file.label
        return str(self.pk)

    @cached_property
    def audio_file(self):
        if self.file_grouper_id:
            return self.file_grouper.file

    def clean(self):
        if (
            self.audio_file and
            self.audio_file.extension not in ALLOWED_EXTENSIONS
        ):
            raise ValidationError(
                ugettext('Incorrect file type: {extension}.').format(
                    extension=self.audio_file.extension
                )
            )

    def get_short_description(self):
        if self.audio_file and self.audio_file.label:
            return self.audio_file.label
        return ugettext('<file is missing>')

    def copy_relations(self, oldinstance):
        # Because we have a ForeignKey, it's required to copy over
        # the reference from the instance to the new plugin.
        self.audio_file = oldinstance.audio_file


class VersionedAudioTrack(CMSPlugin):
    file_grouper = FileGrouperField(
        verbose_name=_('File grouper'),
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name='+',
    )
    kind = models.CharField(
        verbose_name=_('Kind'),
        choices=AudioTrack.KIND_CHOICES,
        max_length=255,
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


def audiofolder_model_get_files(self):
    files = []
    for audio_file in get_files_distinct_grouper_queryset().filter(folder=self.audio_folder):
        if audio_file.extension in ALLOWED_EXTENSIONS:
            files.append(audio_file)
    return files
AudioFolder.get_files = audiofolder_model_get_files  # noqa: E305
