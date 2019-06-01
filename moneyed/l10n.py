# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import re

from babel.numbers import (
    format_currency as babel_format_currency,
    default_locale,
    LC_NUMERIC,
)
from babel.core import Locale
from babel.core import get_global

from moneyed.money import Currency

DEFAULT_LOCALE = default_locale('LC_ALL')


class LocaleDataNotFound(Exception):
    def __init__(self, locale, currency='ALL'):
        super(LocaleDataNotFound, self).__init__(
            "Locale data not found for %s currencies in %s" % (currency, locale)
        )


class LocaleData(object):
    data = {}

    data_providers = []

    @classmethod
    def set_data(cls, currency, name='', sign='', locale=DEFAULT_LOCALE):
        if isinstance(currency, Currency):
            currency = currency.code

        if isinstance(locale, Locale):
            locale = str(locale)

        if not cls.data.get(locale):
            cls.data[locale] = {}

        if not cls.data[locale].get(currency):
            cls.data[locale][currency] = {}

        if name is not None:
            cls.data[locale][currency]['name'] = name

        if sign is not None:
            cls.data[locale][currency]['sign'] = sign

    @classmethod
    def get_data(cls, currency='ALL', locale=DEFAULT_LOCALE):
        if isinstance(locale, Locale):
            locale = str(locale)

        for data_provider in cls.data_providers:
            try:
                return data_provider(currency, locale)
            except LocaleDataNotFound:
                continue

        try:
            data = cls.data[locale]
        except KeyError:
            data = cls.data.get(DEFAULT_LOCALE, None)
            if data is None:
                raise LocaleDataNotFound(locale, currency)

        if isinstance(currency, Currency):
            currency = currency.code

        if currency == 'ALL':
            return data

        try:
            return data[currency]
        except KeyError:
            raise LocaleDataNotFound(locale, currency)

    @classmethod
    def add_data_provider(cls, data_provider):
        if callable(data_provider):
            cls.data_providers += [data_provider]
        else:
            raise TypeError('data_provider should be callable.')


def format_currency(money, locale=LC_NUMERIC, *args, **kwargs):
    try:
        locale_data = LocaleData.get_data(money.currency.code, locale)
    except LocaleDataNotFound:
        locale_data = {}

    if (
        money.currency.code not in get_global('all_currencies').keys()
        or locale_data.get('sign', False)
        or locale_data.get('name', False)
    ):
        locale_object = Locale.parse(locale)

        format = (
            kwargs.pop('format', None)
            or locale_object.currency_formats['standard'].pattern
        )

        name = locale_data.get('name', money.currency.name)
        sign = locale_data.get('sign', money.currency.sign)

        if '¤' in format:
            format = format.replace('¤¤¤', name)
            format = format.replace('¤¤', money.currency.code)
            format = format.replace('¤', sign)

        kwargs['format'] = format

    return babel_format_currency(
        money.amount, money.currency.code, locale=locale, *args, **kwargs
    )


DECIMAL_PLACES_REGEX = re.compile(r'\.0*')


def format_money(
    money,
    include_symbol=True,
    locale=LC_NUMERIC,
    decimal_places=None,
    rounding_method=None,
):
    # FIXME: rounding_method is doing nothing
    locale = Locale.parse(locale)
    format = locale.currency_formats['standard'].pattern
    if not include_symbol:
        format = format.replace('¤', '').strip()
    if decimal_places is not None:
        zeroes = '0' * decimal_places
        format = re.sub(DECIMAL_PLACES_REGEX, '.' + zeroes, format)

    return format_currency(
        money,
        format=format,
        locale=locale,
        currency_digits=False,
        decimal_quantization=True,
    )


set_locale_data = LocaleData.set_data
add_locale_data_provider = LocaleData.add_data_provider
