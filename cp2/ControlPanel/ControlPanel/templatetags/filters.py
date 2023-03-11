from django.template import Library
from datetime import datetime


register = Library()

@register.filter(expects_localtime=True)
def parse_iso(value):
    try:
        return datetime.strptime(value, "%Y-%m-%d %H:%M:%S.%f")
    except Exception:
        return datetime.strptime(value, "%Y-%m-%d %H:%M:%S")