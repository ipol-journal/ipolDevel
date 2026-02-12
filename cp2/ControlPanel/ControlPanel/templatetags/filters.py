from datetime import datetime

from django.template import Library

register = Library()


@register.filter(expects_localtime=True)
def parse_iso(value):
    """Parse several common ISO datetime string formats into a datetime.

    Accepts inputs like:
    - "2026-02-12T09:54:26.879578"
    - "2026-02-12 09:54:26.879578"
    - "2026-02-12T09:54:26"
    - "2026-02-12 09:54:26"
    - "2026-02-12"

    If `value` is already a datetime, it is returned unchanged. If parsing
    fails, the original value is returned.
    """
    if isinstance(value, datetime):
        return value

    formats = (
        "%Y-%m-%dT%H:%M:%S.%f",
        "%Y-%m-%d %H:%M:%S.%f",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d",
    )

    for fmt in formats:
        try:
            return datetime.strptime(value, fmt)
        except Exception:
            continue

    return value
