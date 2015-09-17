# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function, division
import requests
from bs4 import BeautifulSoup
from .log import get_logger

logger = get_logger(__name__)


class SMS(object):

    def __init__(self, service_url, cdkey, password):
        self._service_url = service_url
        self._cdkey = cdkey
        self._password = password

    def send(self, phone_no, msg):
        resp = requests.post(self._service_url, data={
            'cdkey': self._cdkey,
            'password': self._password,
            'phone': phone_no,
            'message': self._build_message(msg)
        })

        if resp.status_code != 200:
            return False

        try:
            bs = BeautifulSoup(resp.content.strip(), 'html.parser')
            return bs.response.error.text == '0'
        except Exception as e:
            logger.exception(e)

        return False


    def _build_message(self, msg):
        return "【绿野】%s" % msg
