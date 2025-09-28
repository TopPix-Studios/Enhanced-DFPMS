from django import template

register = template.Library()


@register.filter
def dict_key(value, key):
    """
    Returns the value of the given key from the dictionary.

    Usage: {{ my_dict|dict_key:key }}
    """
    try:
        return value.get(key, None)
    except (TypeError, AttributeError):
        return None
