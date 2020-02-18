import logging
import warnings

from django import forms
from django.contrib.admin.sites import site
from django.contrib.admin.widgets import ForeignKeyRawIdWidget
from django.db import models
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.http import urlencode
from django.utils.safestring import mark_safe

from djangocms_versioning.helpers import nonversioned_manager
from filer import settings as filer_settings
from filer.models import File
from filer.utils.compatibility import truncate_words
from filer.utils.model_label import get_model_label

from ..models import FileGrouper


logger = logging.getLogger(__name__)


class AdminFileGrouperWidget(ForeignKeyRawIdWidget):
    choices = None

    def render(self, name, value, attrs=None):
        obj = self.obj_for_value(value)
        if obj:
            with nonversioned_manager(File):
                file_obj = obj.file
        else:
            file_obj = None
        css_id = attrs.get('id', 'id_image_x')
        related_url = None
        if value:
            try:
                related_url = file_obj.logical_folder.get_admin_directory_listing_url_path()
            except Exception as e:
                # catch exception and manage it. We can re-raise it for debugging
                # purposes and/or just logging it, provided user configured
                # proper logging configuration
                if filer_settings.FILER_ENABLE_LOGGING:
                    logger.error('Error while rendering file widget: %s', e)
                if filer_settings.FILER_DEBUG:
                    raise
        if not related_url:
            related_url = reverse('admin:filer-directory_listing-last')
        params = self.url_parameters()
        params['_pick'] = 'grouper'
        if params:
            lookup_url = '?' + urlencode(sorted(params.items()))
        else:
            lookup_url = ''
        if 'class' not in attrs:
            # The JavaScript looks for this hook.
            attrs['class'] = 'vForeignKeyRawIdAdminField filer-grouper-filer'
        # rendering the super for ForeignKeyRawIdWidget on purpose here because
        # we only need the input and none of the other stuff that
        # ForeignKeyRawIdWidget adds
        hidden_input = super().render(name, value, attrs)
        context = {
            'hidden_input': hidden_input,
            'lookup_url': '%s%s' % (related_url, lookup_url),
            'object': file_obj,
            'lookup_name': name,
            'id': css_id,
            'admin_icon_delete': 'admin/img/icon-deletelink.svg',
        }
        html = render_to_string('admin/filer/widgets/admin_file.html', context)
        return mark_safe(html)

    def label_for_value(self, value):
        obj = self.obj_for_value(value)
        return '&nbsp;<strong>%s</strong>' % truncate_words(obj, 14)

    def obj_for_value(self, value):
        try:
            key = self.rel.get_related_field().name
            obj = self.rel.to._default_manager.get(**{key: value})
        except:  # noqa
            obj = None
        return obj

    class Media(object):
        css = {
            'all': [
                'filer/css/admin_filer.css',
            ]
        }
        js = (
            'filer/js/libs/dropzone.min.js',
            'filer/js/addons/dropzone.init.js',
            'filer/js/addons/popup_handling.js',
            'filer/js/addons/widget.js',
        )


class AdminFileGrouperFormField(forms.ModelChoiceField):
    widget = AdminFileGrouperWidget

    def __init__(self, rel, queryset, *args, **kwargs):
        self.rel = rel
        self.queryset = queryset
        self.max_value = None
        self.min_value = None
        kwargs.pop('widget', None)
        super().__init__(queryset, widget=self.widget(rel, site), *args, **kwargs)

    def widget_attrs(self, widget):
        widget.required = self.required
        return {}

    def to_python(self, value):
        # Filter out any repeated values for the grouper
        self.queryset = self.queryset.distinct()
        obj = super().to_python(value)
        if not obj:
            return obj
        with nonversioned_manager(File):
            obj._prefetched_objects_cache = {'files': [obj.file]}
        return obj


class FileGrouperField(models.ForeignKey):
    default_form_class = AdminFileGrouperFormField
    default_model_class = FileGrouper

    def __init__(self, **kwargs):
        # We hard-code the `to` argument for ForeignKey.__init__
        dfl = get_model_label(self.default_model_class)
        if "to" in kwargs.keys():  # pragma: no cover
            old_to = get_model_label(kwargs.pop("to"))
            if old_to != dfl:
                msg = "%s can only be a ForeignKey to %s; %s passed" % (
                    self.__class__.__name__, dfl, old_to
                )
                warnings.warn(msg, SyntaxWarning)
        kwargs['to'] = dfl
        super().__init__(**kwargs)

    def formfield(self, **kwargs):
        # This is a fairly standard way to set up some defaults
        # while letting the caller override them.
        # rel was changed into remote_field in django 2.x
        remote_field = self.rel if hasattr(self, 'rel') else self.remote_field
        defaults = {
            'form_class': self.default_form_class,
            'rel': remote_field,
            'to_field_name': 'files__grouper_id',
        }
        defaults.update(kwargs)
        return super().formfield(**defaults)
