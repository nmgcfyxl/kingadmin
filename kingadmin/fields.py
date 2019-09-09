#! /usr/bin/env python
# -*- coding: utf-8 -*-
# @Author   :yangxiaolong
# @Email    :nmgcfyxl@163.com
# @Date     :2019/9/8

import inspect

from django.core.exceptions import ObjectDoesNotExist
from django.template import loader
from django.utils import six
from django.utils.safestring import mark_safe


class Empty:
    """
    This class is used to represent no data being provided for a given input
    or output value.

    It is required because `None` may be a valid input or output value.
    """
    pass


def is_simple_callable(obj):
    """
    True if the object is a callable that takes no arguments.
    """
    if not (inspect.isfunction(obj) or inspect.ismethod(obj)):
        return False

    sig = inspect.signature(obj)
    params = sig.parameters.values()
    return all(
        param.kind == param.VAR_POSITIONAL or
        param.kind == param.VAR_KEYWORD or
        param.default != param.empty
        for param in params
    )


def get_attribute(instance, attrs):
    """
    Similar to Python's built in `getattr(instance, attr)`,
    but takes a list of nested attributes, instead of a single attribute.

    Also accepts either attribute lookup on objects or dictionary lookups.
    """
    for attr in attrs:
        if instance is None:
            # Break out early if we get `None` at any point in a nested lookup.
            return None
        try:
            instance = getattr(instance, attr)
        except ObjectDoesNotExist:
            return None

        if is_simple_callable(instance):
            try:
                instance = instance()
            except (AttributeError, KeyError) as exc:
                raise ValueError(
                    'Exception raised in callable attribute "{0}"; original exception was: {1}'.format(attr, exc))

    return instance


class Field(object):

    def __init__(self, default=Empty, initial=Empty, source=None,
                 label=None, help_text=None, style=None,
                 error_messages=None, verbose_name=""):

        self.default = default
        self.source = source
        self.initial = initial if (initial is Empty) else initial
        self.label = label
        self.help_text = help_text
        self.style = style
        self.error_messages = error_messages
        self.verbose_name = verbose_name

        self.field_name = None
        self.parent = None
        self.source_attrs = []

    def bind(self, field_name, parent):
        """
        初始化字段实例的字段名称和父字段.
        当字段被添加到父序列化器实例时调用.
        """
        # my_field = serializer.CharField(source='my_field')
        assert self.source != field_name, (
                "It is redundant to specify `source='%s'` on field '%s' in "
                "serializer '%s', because it is the same as the field name. "
                "Remove the `source` keyword argument." %
                (field_name, self.__class__.__name__, parent.__class__.__name__)
        )

        self.field_name = field_name
        self.parent = parent

        # `self.label` should default to being based on the field name.
        if self.label is None:
            self.label = field_name.replace("", " ").capitalize()

        # self.source should default to being the same as the field name.
        if self.source is None:
            self.source = field_name

        # self.source_attrs is a list of attributes that need to be looked up
        # when serializing the instance, or populating the validated data.
        if self.source == "*":
            self.source_attrs = []
        else:
            self.source_attrs = self.source.split(".")

    def get_attribute(self, instance):
        return get_attribute(instance, self.source_attrs)

    def to_representation(self, value):
        """自定义方法接口

        """
        raise NotImplementedError(
            '{cls}.to_representation() must be implemented for field '
            '{field_name}. If you do not need to support write operations '
            'you probably want to subclass `ReadOnlyField` instead.'.format(
                cls=self.__class__.__name__,
                field_name=self.field_name,
            )
        )


# String types...


class StringField(Field):

    def to_representation(self, value):
        return six.text_type(value)


class HtmlField(Field):

    def __init__(self, template=None, **kwargs):
        self.template = template
        super(HtmlField, self).__init__(**kwargs)

    def to_representation(self, value):
        return mark_safe(
            loader.render_to_string(
                self.template,
                context={
                    self.field_name: value
                }
            )
        )


class ImgHtmlField(Field):
    """img path field

    """

    def __init__(self, img_domain=None, width="100%", height="100%", **kwargs):
        self.img_domain = img_domain
        self.width, self.height = width, height
        super(ImgHtmlField, self).__init__(**kwargs)

    def to_representation(self, value):
        return f"<img src='{self.img_domain}{value if value.startswith('') else f'/{value}'}' " \
               f"width={self.width} height={self.height} />"


# Miscellaneous field types...


class MethodField(Field):

    def __init__(self, method_name=None, **kwargs):
        self.method_name = method_name
        kwargs["source"] = "*"
        super(MethodField, self).__init__(**kwargs)

    def bind(self, field_name, parent):
        default_method_name = f"get_{field_name}"

        # The method name should default to `get_{field_name}`.
        if self.method_name is None:
            self.method_name = default_method_name

        super(MethodField, self).bind(field_name, parent)

    def to_representation(self, value):
        method = getattr(self.parent, self.method_name)
        return method(value)
