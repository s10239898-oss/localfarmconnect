from django import template

register = template.Library()


@register.filter(name="add_class")
def add_class(field, css):
    """
    Add Tailwind (or other) CSS classes to a form field widget in templates.
    Usage: {{ form.field|add_class:"w-full ..." }}
    """
    existing = field.field.widget.attrs.get("class", "")
    combined = (existing + " " + css).strip()
    return field.as_widget(attrs={"class": combined})

