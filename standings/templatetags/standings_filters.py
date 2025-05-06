from django import template
from django.http import QueryDict

register = template.Library()

@register.simple_tag(takes_context=True)
def preserve_filters_url(context, type_value):
    """
    Creates a URL that preserves all current filters while changing the type parameter.
    """
    request = context['request']
    params = request.GET.copy()
    params['type'] = type_value
    return f"?{params.urlencode()}" 