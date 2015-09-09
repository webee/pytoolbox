# coding=utf-8
from __future__ import unicode_literals

import urllib
import urlparse


def build_url(base_url, *args, **kwargs):

    parts = urlparse.urlparse(base_url)

    target_params = urlparse.parse_qs(parts.query, keep_blank_values=True)
    # expect args to be dicts.
    added_params = [params for params in args]
    added_params.append(kwargs)

    for params in added_params:
        for k, v in params.items():
            target_params.setdefault(k, []).append(v)

    parts = list(parts)
    #[0]scheme, [1]netloc, [2]path, [3]params, [4]query, [5]fragment
    parts[4] = urllib.urlencode(target_params, doseq=True)

    return urlparse.urlunparse(parts)


def extract_query_params(url):
    """
    http://a.b.c/d/?a=1&b=2&c=3&a=11
    => {'a': '11', 'b': '2', 'c': '3'}
    multi values, get the last one.
    :param url:
    :return:
    """
    parts = urlparse.urlparse(url)

    pairs = urlparse.parse_qsl(parts.query)

    return {k: v for k, v in pairs}
