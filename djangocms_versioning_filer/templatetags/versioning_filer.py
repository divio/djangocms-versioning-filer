from django import template


register = template.Library()


@register.simple_tag(takes_context=True)
def get_url(context, file):
    toolbar = context.get('cms_toolbar')
    current_url = context.get('current_url', '')

    if (not toolbar or not toolbar.edit_mode_active) and 'admin' not in current_url:
        return file.url

    return file.file.url
