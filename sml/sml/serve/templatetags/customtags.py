
from functools import reduce
from django import template

register = template.Library()

@register.filter(name='phone')
def phone(value):
    phone = '(%s) %s-%s' %(value[0:3],value[3:6],value[6:10])
    return phone

@register.filter(name='duration')
def duration(value):
    months = int(value.days / 30)
    weeks = int(value.days / 7)

    if months:
        if months > 24:
            return '{} {}'.format(int(months / 12), 'years')

        return '{} {}'.format(months, 'month' if months == 1 else 'months')
    elif weeks:
        return '{} {}'.format(weeks, 'week' if weeks == 1 else 'weeks')
    else:
        return '{} days'.format(value.days)

@register.filter(name='tuple_lookup')
def tuple_lookup(value, iterable):
    for key, name in iterable:
        if key == value:
            return name
    else:
        return 'unknown'


@register.filter(name='filter_none')
def filter_none(iterable, field):
    return [i for i in iterable if getattr(i, field) is not None]


@register.filter(name='filter_not_none')
def filter_not_none(iterable, field):
    return [i for i in iterable if getattr(i, field) is None]


@register.filter(name='filter_true')
def filter_true(iterable, field):
    return [i for i in iterable if getattr(i, field) is True]


@register.filter(name='filter_false')
def filter_false(iterable, field):
    return [i for i in iterable if getattr(i, field) is False]


@register.filter(name='filter_value')
def filter_value(iterable,pair):
    name, value = pair.split(',')
    return [i for i in iterable if getattr(i, name) == value]

@register.filter(name='finances_summary')
def finances_summary(iterable):
    total = reduce(lambda t,c: t + c.amount if c.category.name == 'Income' else t - c.amount, iterable, 0)
    return ('surplus', total) if total >= 0 else ('deficit', total)

@register.filter(name='flatten')
def flatten(first, second):
    return [item for sublist in [first, second] for item in sublist]
