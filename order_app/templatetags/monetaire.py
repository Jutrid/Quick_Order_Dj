from django import template

register = template.Library()


def _sep(value):
    try:
        nombre = int(round(float(value)))
    except (TypeError, ValueError):
        return value
    return format(nombre, ',').replace(',', ' ')


@register.filter(is_safe=True)
def sep(value):
    return _sep(value)


@register.filter(is_safe=True)
def montant(value):
    return f'{_sep(value)} CDF'
