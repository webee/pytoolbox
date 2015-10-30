# coding=utf-8
from __future__ import unicode_literals, print_function
import sys
import inspect
from .. import runtime, mods


def route(pattern, *args, **kwargs):
    # noinspection PyPackageRequirements
    from django.conf.urls import patterns, url
    # noinspection PyPackageRequirements
    from django.views import generic

    views_mod = runtime.current_module(1)
    p = __import__(views_mod.__package__)
    # find urls mod.
    urls_mod = mods.find_mod(p, 'urls')

    prefix = ''
    if hasattr(urls_mod, 'prefix'):
        prefix = urls_mod.prefix

    def _wrapper(f):
        if urls_mod:
            if not hasattr(urls_mod, 'urlpatterns'):
                urls_mod.urlpatterns = []
            if inspect.isfunction(f):
                urls_mod.urlpatterns += patterns(prefix, url(pattern, f, **kwargs))
            elif inspect.isclass(f) and issubclass(f, generic.View):
                urls_mod.urlpatterns += patterns(prefix, url(pattern, f.as_view(), *args, **kwargs))
            else:
                print("view type not exists: {0}.".format(f))
                sys.exit(1)
        return f

    return _wrapper
