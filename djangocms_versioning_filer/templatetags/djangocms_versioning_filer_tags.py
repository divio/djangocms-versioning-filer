from collections import ChainMap

from django import template
from django.apps import apps


register = template.Library()


@register.simple_tag
def get_versioning_filer_admin_actions():
    """
    :returns: Configured list of file_changelist_actions compiled by the app config
    """
    app_config = apps.get_app_config("djangocms_versioning_filer").cms_extension
    return app_config.file_changelist_actions
