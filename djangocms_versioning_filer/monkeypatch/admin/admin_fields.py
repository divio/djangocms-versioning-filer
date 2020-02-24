"""
Regarding the monkeypatching that happens in this file. There is a fair amount
of code being pulled in from django-filer which is unrelated to the actual
monkeypatching that needs to happen.

The following is what has been changed.

file_obj = File._original_manager.get(pk=value)
obj = self.rel.model._original_manager.get(**{key: value})
queryset = remove_published_where(queryset)
qs = self.remote_field.model._original_manager.using(using).filter(
    **{self.remote_field.field_name: value}
)

The code that is patched is from the following commit
https://github.com/divio/django-filer/tree/655ead261d124cf5b943abdcf30c7921aa20374f

To avoid pulling in so much code it would have been better to write
small utility methods that gets the object for filer that then can be patched
by versioning-filer.
"""

import logging

from django.contrib.admin.widgets import ForeignKeyRawIdWidget
from django.db.models import ForeignKey
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.http import urlencode
from django.utils.safestring import mark_safe

import filer
from djangocms_versioning.helpers import remove_published_where
from filer import settings as filer_settings
from filer.fields.file import AdminFileFormField
from filer.models.filemodels import File


logger = logging.getLogger(__name__)


def render(self, name, value, attrs=None, renderer=None):
    obj = self.obj_for_value(value)
    css_id = attrs.get('id', 'id_image_x')
    related_url = None
    if value:
        try:
            # We need to get the original manager to be able to access drafts.
            file_obj = File._original_manager.get(pk=value)
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
    params['_pick'] = 'file'
    if params:
        lookup_url = '?' + urlencode(sorted(params.items()))
    else:
        lookup_url = ''
    if 'class' not in attrs:
        # The JavaScript looks for this hook.
        attrs['class'] = 'vForeignKeyRawIdAdminField'
    # rendering the super for ForeignKeyRawIdWidget on purpose here because
    # we only need the input and none of the other stuff that
    # ForeignKeyRawIdWidget adds
    hidden_input = super(ForeignKeyRawIdWidget, self).render(name, value, attrs)
    context = {
        'hidden_input': hidden_input,
        'lookup_url': '%s%s' % (related_url, lookup_url),
        'object': obj,
        'lookup_name': name,
        'id': css_id,
        'admin_icon_delete': ('admin/img/icon-deletelink.svg'),
    }
    html = render_to_string('admin/filer/widgets/admin_file.html', context)
    return mark_safe(html)


def obj_for_value(self, value):
    if value:
        try:
            key = self.rel.get_related_field().name
            # we need the original manager to access draft
            obj = self.rel.model._original_manager.get(**{key: value})
        except Exception:
            obj = None
    else:
        obj = None
    return obj


init = AdminFileFormField.__init__


def __init__(self, rel, queryset, to_field_name, *args, **kwargs):
    queryset = remove_published_where(queryset)
    init(self, rel, queryset, to_field_name, *args, **kwargs)


def validate(self, value, model_instance):
    from django.core import exceptions
    from django.db import router
    if self.remote_field.parent_link:
        return
    super(ForeignKey, self).validate(value, model_instance)
    if value is None:
        return

    using = router.db_for_read(self.remote_field.model, instance=model_instance)
    # we need to use the original manager to access drafts
    qs = self.remote_field.model._original_manager.using(using).filter(
        **{self.remote_field.field_name: value}
    )
    qs = qs.complex_filter(self.get_limit_choices_to())
    if not qs.exists():
        raise exceptions.ValidationError(
            self.error_messages['invalid'],
            code='invalid',
            params={
                'model': self.remote_field.model._meta.verbose_name, 'pk': value,
                'field': self.remote_field.field_name, 'value': value,
            },  # 'pk' is included for backwards compatibility
        )


filer.fields.file.AdminFileWidget.render = render
filer.fields.file.AdminFileWidget.obj_for_value = obj_for_value
filer.fields.file.AdminFileFormField.__init__ = __init__
filer.fields.file.FilerFileField.validate = validate
