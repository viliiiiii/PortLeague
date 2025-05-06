from django import template
from django.http import QueryDict

register = template.Library()

@register.simple_tag(takes_context=True)
def preserve_filters_gameweek(context, gameweek):
    """
    Creates a URL that preserves all current filters while changing the gameweek parameter.
    """
    request = context['request']
    params = request.GET.copy()
    params['gameweek'] = gameweek
    return f"?{params.urlencode()}" 