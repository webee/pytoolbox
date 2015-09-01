# coding=utf-8
from __future__ import unicode_literals
from functools import wraps
from decimal import Decimal

import os
import requests
from collections import namedtuple
from ..util.sign import SignType, Signer
from ..util import pmc_config, public_key, aes
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


def _submit_form(url, req_params, method='POST'):
    submit_page = '<form id="formName" action="{0}" method="{1}">'.format(url, method)
    for key in req_params:
        submit_page += '''<input type="hidden" name="{0}" value='{1}' />'''.format(key, req_params[key])
    submit_page += '<input type="submit" value="Submit" style="display:none" /></form>'
    submit_page += '<script>document.forms["formName"].submit();</script>'
    return submit_page


class PayClient(object):

    def __init__(self):
        self.config = Config()
        self.signer = Signer('key', 'sign')
        self.channel_pri_key = None
        self._uid_accounts = {}

    def init_config(self, env_config):
        pmc_config.merge_config(self.config, env_config)
        # 这里的主要作用是签名, 只需要channel_pri_key或md5_key
        self.signer.init(self.config.MD5_KEY, self.config.CHANNEL_PRI_KEY, None)
        self.channel_pri_key = public_key.loads_b64encoded_key(self.config.CHANNEL_PRI_KEY)

    def verify_request(self, f):
        from flask import request

        @wraps(f)
        def wrapper(*args, **kwargs):
            try:
                data = {}
                data.update(request.values.items())
                data.update(request.view_args)
                logger.info('receive request [{0}] [{1}]: [{2}]'.format(request.method, request.url, data))
                # check channel
                channel_name = data.get('channel_name')
                if channel_name != self.config.CHANNEL_NAME:
                    is_verify_pass = False
                else:
                    # verify sign
                    lvye_aes_key = self.channel_pri_key.decrypt_from_base64(data['_lvye_aes_key'])
                    lvye_pub_key = aes.decrypt_from_base64(data['_lvye_pub_key'], lvye_aes_key)
                    # 主要用来验签
                    signer = Signer('key', 'sign', self.config.MD5_KEY, None, lvye_pub_key)
                    sign_type = data['sign_type']
                    is_verify_pass = signer.verify(data, sign_type)
            except Exception as e:
                logger.exception(e)
                is_verify_pass = False

            logger.info("[{0}] verify done.".format(request.url))
            request.__dict__['is_verify_pass'] = is_verify_pass
            request.__dict__['params'] = data
            return f(*args, **kwargs)
        return wrapper

    def _generate_api_url(self, url, **kwargs):
        url = url.lstrip('/')
        return os.path.join(self.config.ROOT_URL, url.format(**kwargs))

    def _add_sign_to_params(self, params, sign_type=SignType.RSA):
        params['sign_type'] = sign_type
        params['channel_name'] = self.config.CHANNEL_NAME
        params['sign'] = self.signer.sign(params, sign_type)

        return params

    def request(self, url, params=None, sign_type=SignType.RSA, method='post'):
        if params is None:
            params = {}

        params = self._add_sign_to_params(params, sign_type)

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

    def prepaid(self, to_user_id, amount, to_domain_name="", callback_url="", notify_url=""):
        params = {
            'to_user_id': to_user_id,
            'to_domain_name': to_domain_name,
            'amount': amount,
            'callback_url': callback_url,
            'notify_url': notify_url
        }

        url = self._generate_api_url(self.config.PREPAID_URL)
        params = self._add_sign_to_params(params)
        return _submit_form(url, params)

    def prepay(self, params, ret_sn=False):
        params = dict(params)
        url = self._generate_api_url(self.config.PREPAY_URL)
        result = self.post_req(url, params)
        if _is_success_result(result):
            if ret_sn:
                return result.data['sn']
            return result.data['pay_url']
        return None

    def zyt_pay(self, sn):
        params = {
            'sn': sn
        }
        url = self._generate_api_url(self.config.ZYT_PAY_URL, **params)

        params = self._add_sign_to_params(params)
        return _submit_form(url, params)

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

    def query_withdraw(self, user_id, sn, ret_result=False):
        params = {
            'user_id': user_id,
            'sn': sn
        }

        url = self._generate_api_url(self.config.QUERY_WITHDRAW_URL, **params)
        result = self.get_req(url, params)
        if ret_result:
            return result

        if _is_success_result(result):
            return result.data['data']
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

    def app_get_user_bankcard(self, user_id, bankcard_id):
        params = {'user_id': user_id, 'bankcard_id': bankcard_id}

        url = self._generate_api_url(self.config.APP_GET_USER_BANKCARD_URL, **params)
        result = self.get_req(url, params)

        if _is_success_result(result):
            return result.data['data']
        return None

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
