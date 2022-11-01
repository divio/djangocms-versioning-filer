from django import template
from django.apps import apps
from django.urls import reverse

from djangocms_versioning.constants import DRAFT, PUBLISHED
from djangocms_versioning.helpers import proxy_model


register = template.Library()


def _get_version(content):
    """
    Method to return the latest version, or null, given content
    :param: content: Content Object
    :returns: Version or None
    """
    return content.versions.first()


@register.simple_tag
def get_versioning_filer_admin_actions():
    """
    :returns: Configured list of file_changelist_actions compiled by the app config
    """
    app_config = apps.get_app_config("djangocms_versioning_filer").cms_extension
    return app_config.file_changelist_actions


@register.simple_tag
def get_versioning_filer_edit_url(file):
    """
    Given a file, return an edit endpoint url for it, if there is a version associated with it,
    and it is in a state which allows editing.
    :param: file: Filer File model
    :returns: Edit URL or empty string
    """
    version = _get_version(file)
    # Fallback to empty string if version couldn't be found
    if not version:
        return ""
    version = proxy_model(version, file._meta.model)
    if version.state not in (DRAFT, PUBLISHED):
        # Don't display the link if it cannot be edited
        return ""
    return reverse(
        "admin:{app}_{model}_edit_redirect".format(
            app=version._meta.app_label,
            model=version._meta.model_name,
        ),
        args=(version.pk, ),
    )


@register.simple_tag
def get_versioning_filer_edit_disabled(file, request):
    """
    Check whether a given file can be edited, disable if not.
    :param: file: Filer File model
    :param: request: Request object
    :returns: Boolean indicating whether edit link should be disabled
    """
    version = _get_version(file)
    if not version:
        return True
    if version.check_edit_redirect.as_bool(request.user):
        return False
    return True
