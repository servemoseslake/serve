
from datetime import datetime, date


def date_from_string(value, format='%Y-%m-%d'):
    if type(value) == date:
        return value

    return datetime.strptime(value, format).date()


def datetime_from_string(value, format='%Y-%m-%dT%H:%M'):
    alternate_formats = (
        '%Y-%m-%dT%H:%M:%S',
    )

    all_formats = set((format,) + alternate_formats)

    for fmt in all_formats:
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            pass

    raise ValueError


def date_to_age(value, now=None):
    now = now if now else datetime.now()

    if value > now.date().replace(year = value.year):
        return now.date().year - value.year - 1
    else:
        return now.date().year - value.year

def datetime_round(value):
    return datetime(value.year, value.month, value.day, value.hour, tzinfo=value.tzinfo)


