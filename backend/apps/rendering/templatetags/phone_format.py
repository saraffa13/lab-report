from django import template

register = template.Library()


@register.filter(name="india_phone")
def india_phone(value):
    """Prefix '+91 ' to an Indian phone unless it already starts with '+'."""
    if not value:
        return ""
    s = str(value).strip()
    if not s:
        return ""
    if s.startswith("+"):
        return s
    return f"+91 {s}"
