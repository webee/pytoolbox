# coding=utf-8
from __future__ import unicode_literals
from functools import wraps
from decimal import Decimal

import os
import requests
from collections import namedtuple
from ..util.sign import SignType, Signer
from ..util import pmc_config
from ..util.log import get_logger
from ..util.urls import build_url
from .config import Config


logger = get_logger(__name__)
Result = namedtuple('Result', 'status_code, data')


def _is_success_result(result):
    if result is None:
        return False
    ret = result.data['ret']
    if not ret:
        logger.warn("failed result: code: {0}, msg: {1}, data: {2}".format(result.data['code'],
                                                                           result.data['msg'], result.data))
    return ret


class PayClient(object):

    def __init__(self):
        self.config = Config()
        self.signer = Signer('key', 'sign')
        self._uid_accounts = {}

    def init_config(self, env_config):
        pmc_config.merge_config(self.config, env_config)
        self.signer.init(self.config.MD5_KEY, self.config.CHANNEL_PRI_KEY, self.config.LVYE_PUB_KEY)

    def verify_request(self, f):
        from flask import request

        @wraps(f)
        def wrapper(*args, **kwargs):
            try:
                data = {}
                data.update(request.values.items())
                data.update(request.view_args)
                logger.info('receive request [0] [0]: [{1}]'.format(request.method, request.url, data))
                # check channel
                channel_name = data.get('channel_name')
                if channel_name != self.config.CHANNEL_NAME:
                    is_verify_pass = False
                else:
                    # verify sign
                    sign_type = data['sign_type']
                    is_verify_pass = self.signer.verify(data, sign_type)
            except Exception as e:
                logger.exception(e)
                is_verify_pass = False

            request.__dict__['is_verify_pass'] = is_verify_pass
            request.__dict__['params'] = data
            return f(*args, **kwargs)
        return wrapper

    def _generate_api_url(self, url, **kwargs):
        url = url.lstrip('/')
        return os.path.join(self.config.ROOT_URL, url.format(**kwargs))

    def request(self, url, params=None, sign_type=SignType.RSA, method='post'):
        if params is None:
            params = {}

        params['sign_type'] = sign_type
        params['channel_name'] = self.config.CHANNEL_NAME
        params['sign'] = self.signer.sign(params, sign_type)

        try:
            logger.info("request {0} {1}: {2}".format(method, url, params))
            req = requests.request(method, url, data=params)
            try:
                if req.status_code != 200:
                    logger.warn('failed request result: [{0}], [{1}]'.format(req.status_code, req.text))
                logger.debug('request result: [{0}], [{1}]'.format(req.status_code, req.text))
                return Result(req.status_code, req.json())
            except Exception as e:
                logger.exception(e)
                return None
        except Exception as e:
            logger.exception(e)
        return None

    def get_req(self, url, params=None):
        return self.request(url, params, method='get')

    def post_req(self, url, params=None):
        return self.request(url, params, method='post')

    def query_user_is_opened(self, user_id):
        params = {
            'user_id': user_id
        }

        url = self._generate_api_url(self.config.QUERY_USER_IS_OPENED_URL, **params)

        result = self.get_req(url, params)
        if _is_success_result(result):
            return result.data['is_opened']
        return False

    def get_account_user(self, user_id):
        if user_id not in self._uid_accounts:
            params = {
                'user_id': user_id
            }
            url = self._generate_api_url(self.config.GET_ACCOUNT_USER_URL, **params)
            result = self.get_req(url, params)
            if _is_success_result(result):
                self._uid_accounts[user_id] = result.data['account_user_id']
        return self._uid_accounts.get(user_id)

    def get_create_account_user(self, user_id):
        if user_id not in self._uid_accounts:
            params = {
                'user_id': user_id
            }
            url = self._generate_api_url(self.config.GET_CREATE_ACCOUNT_USER_URL, **params)
            result = self.post_req(url, params)
            if _is_success_result(result):
                self._uid_accounts[user_id] = result.data['account_user_id']
        return self._uid_accounts.get(user_id)

    def prepay(self, params):
        params = dict(params)
        url = self._generate_api_url(self.config.PREPAY_URL)
        result = self.post_req(url, params)
        if _is_success_result(result):
            return result.data['pay_url']
        return None

    def confirm_guarantee_payment(self, order_id, ret_result=False):
        params = {
            'order_id': order_id
        }

        url = self._generate_api_url(self.config.CONFIRM_GUARANTEE_PAYMENT_URL)
        result = self.post_req(url, params)

        if ret_result:
            return result

        return _is_success_result(result)

    def refund(self, order_id=None, amount=None, notify_url=None, params=None, ret_result=False):
        if params is None:
            params = {
                'order_id': order_id,
                'amount': amount,
                'notify_url': notify_url
            }
        else:
            params = dict(params)

        url = self._generate_api_url(self.config.REFUND_URL)
        result = self.post_req(url, params)
        if ret_result:
            return result

        if _is_success_result(result):
            return result.data['sn']
        return None

    def withdraw(self, user_id, params, ret_result=False):
        params = dict(params)
        params['user_id'] = user_id

        url = self._generate_api_url(self.config.WITHDRAW_URL, user_id=user_id)
        result = self.post_req(url, params)
        if ret_result:
            return result

        if _is_success_result(result):
            return result.data
        return None

    def list_transactions(self, user_id, role, page_no, page_size, q):
        url = self._generate_api_url(self.config.LIST_USER_TRANSACTIONS_URL, user_id=user_id)

        params = {
            'role': role,
            'page_no': page_no,
            'page_size': page_size
        }
        if q:
            params['q'] = q

        url = build_url(url, **params)

        params['user_id'] = user_id
        result = self.get_req(url, params)

        if _is_success_result(result):
            return result.data['data']
        return None

    def app_query_bin(self, card_no):
        params = {
            'card_no': card_no
        }
        url = self._generate_api_url(self.config.APP_QUERY_BIN_URL, **params)

        result = self.get_req(url, params)
        if _is_success_result(result):
            return result.data['data']
        return None

    def app_bind_bankcard(self, user_id, params=None, ret_result=False):
        params = dict(params)
        params['user_id'] = user_id

        url = self._generate_api_url(self.config.APP_BIND_BANKCARD_URL, user_id=user_id)
        result = self.post_req(url, params)
        if ret_result:
            return result

        if _is_success_result(result):
            return result.data['id']
        return None

    def app_unbind_bankcard(self, user_id, bankcard_id):
        params = {
            'user_id': user_id,
            'bankcard_id': bankcard_id
        }

        url = self._generate_api_url(self.config.APP_UNBIND_BANKCARD_URL, **params)
        result = self.post_req(url, params)

        return _is_success_result(result)

    def app_list_user_bankcards(self, user_id):
        params = {'user_id': user_id}

        url = self._generate_api_url(self.config.APP_LIST_USER_BANKCARDS_URL, **params)
        result = self.get_req(url, params)

        if _is_success_result(result):
            return result.data['data']
        return None

    def app_withdraw(self, user_id, bankcard_id=None, amount=None, notify_url=None, params=None, ret_result=False):
        if params is None:
            params = {
                'user_id': user_id,
                'bankcard_id': bankcard_id,
                'amount': amount,
                'notify_url': notify_url
            }
        else:
            params = dict(params)
            params['user_id'] = user_id

        url = self._generate_api_url(self.config.APP_WITHDRAW_URL, user_id=user_id)
        result = self.post_req(url, params)
        if ret_result:
            return result

        if _is_success_result(result):
            return result.data
        return None

    def app_query_user_balance(self, user_id):
        params = {
            'user_id': user_id
        }
        url = self._generate_api_url(self.config.APP_QUERY_USER_BALANCE_URL, **params)
        result = self.get_req(url, params)

        if _is_success_result(result):
            return result.data['data']
        return {'total': Decimal(0), 'available': Decimal(0), 'frozen': Decimal(0)}

    def app_query_user_available_balance(self, user_id):
        return self.app_query_user_balance(user_id)['available']
