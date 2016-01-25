# coding=utf-8
from __future__ import unicode_literals

from collections import namedtuple
from decimal import Decimal
from functools import wraps

import os
import requests
from . import constant
from .utils import is_success_result, submit_form, which_to_return
from .config import Config
from ..util import pmc_config, public_key, aes
from ..util.log import get_logger
from ..util.sign import SignType, Signer
from ..util.urls import build_url, extract_query_params

logger = get_logger(__name__)
Result = namedtuple('Result', 'status_code, data')


class PayClient(object):
    constant = constant

    def __init__(self, env_config=None):
        self.config = Config()
        self.signer = Signer('key', 'sign')
        self.channel_pri_key = None
        self._uid_accounts = {}
        self._accepted_channel_clients = {}

        if env_config is not None:
            self.init_config(env_config)

    def init_config(self, env_config):
        pmc_config.merge_config(self.config, env_config)
        # 这里的主要作用是签名, 只需要channel_pri_key或md5_key
        self.signer.init(self.config.MD5_KEY, self.config.CHANNEL_PRI_KEY, None)
        self.channel_pri_key = public_key.loads_b64encoded_key(self.config.CHANNEL_PRI_KEY)

    def setup_accepted_clients(self, clients):
        for client in clients:
            self._accepted_channel_clients[client.config.CHANNEL_NAME] = client

    def _get_current_client(self, channel_name):
        client = self
        if self._accepted_channel_clients:
            client = self._accepted_channel_clients.get(channel_name)
        if channel_name != client.config.CHANNEL_NAME:
            return None
        return client

    def _do_verify_request(self, method, url, data):
        try:
            logger.info('receive request [{0}] [{1}]: [{2}]'.format(method, url, data))
            # check channel
            channel_name = data.get('channel_name')
            # find the correct client
            client = self._get_current_client(channel_name)
            if client is None or channel_name != client.config.CHANNEL_NAME:
                is_verify_pass = False
            else:
                # verify sign
                lvye_aes_key = client.channel_pri_key.decrypt_from_base64(data['_lvye_aes_key'])
                lvye_pub_key = aes.decrypt_from_base64(data['_lvye_pub_key'], lvye_aes_key)
                # 主要用来验签
                signer = Signer('key', 'sign', client.config.MD5_KEY, None, lvye_pub_key)
                sign_type = data['sign_type']
                is_verify_pass = signer.verify(data, sign_type)
        except Exception as e:
            logger.exception(e)
            is_verify_pass = False

        logger.info("[{0}] verify done.".format(url))
        return is_verify_pass

    def verify_request_generic(self, get_ctx, set_ctx=None, fail_verify_handler=None):
        def verify_request(f):
            @wraps(f)
            def wrapper(*args, **kwargs):
                method, url, params = get_ctx(*args, **kwargs)
                is_verify_pass = self._do_verify_request(method, url, params)

                if not is_verify_pass and fail_verify_handler:
                    return fail_verify_handler(params, *args, **kwargs)

                if set_ctx:
                    set_ctx(is_verify_pass, params)
                    return f(*args, **kwargs)
                return f(is_verify_pass, params, *args, **kwargs)
            return wrapper
        return verify_request

    def verify_request(self, f):
        """ for flask
        :param f:
        """
        from flask import request

        def get_ctx():
            data = {}
            data.update(request.values.items())
            data.update(request.view_args)

            return request.method, request.url, data

        def set_ctx(is_verify_pass, params):
            request.__dict__['is_verify_pass'] = is_verify_pass
            request.__dict__['params'] = params

        return self.verify_request_generic(get_ctx, set_ctx)(f)

    def _generate_api_url(self, url, **kwargs):
        url = url.lstrip('/')
        return os.path.join(self.config.ROOT_URL, url.format(**kwargs))

    def _add_sign_to_params(self, params, sign_type=SignType.RSA):
        params['sign_type'] = sign_type
        params['channel_name'] = self.config.CHANNEL_NAME
        params['sign'] = self.signer.sign(params, sign_type)

        return params

    @staticmethod
    def is_success_result(result):
        return is_success_result(result)

    @staticmethod
    def _do_request(url, params=None, method='get'):
        try:
            logger.info("request {0} {1}: {2}".format(method, url, params))
            req = requests.request(method, url, data=params)
            try:
                if req.status_code != 200:
                    logger.warn('failed request result: [{0}], [{1}]'.format(req.status_code, req.text))
                logger.debug('request result: [{0}], [{1}]'.format(req.status_code, req.text))
                return Result(req.status_code, req.json(use_decimal=True))
            except Exception as e:
                logger.exception(e)
                return None
        except Exception as e:
            logger.exception(e)
        return None

    def request(self, url, params=None, sign_type=SignType.RSA, method='post'):
        if params is None:
            params = {}

        params.update(extract_query_params(url))
        params = self._add_sign_to_params(params, sign_type)

        return self._do_request(url, params, method=method)

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
        if is_success_result(result):
            return result.data['is_opened']
        return False

    def get_account_user(self, user_id):
        if user_id not in self._uid_accounts:
            params = {
                'user_id': user_id
            }
            url = self._generate_api_url(self.config.GET_ACCOUNT_USER_URL, **params)
            result = self.get_req(url, params)
            if is_success_result(result):
                self._uid_accounts[user_id] = result.data['account_user_id']
        return self._uid_accounts.get(user_id)

    def get_create_account_user(self, user_id):
        if user_id not in self._uid_accounts:
            params = {
                'user_id': user_id
            }
            url = self._generate_api_url(self.config.GET_CREATE_ACCOUNT_USER_URL, **params)
            result = self.post_req(url, params)
            if is_success_result(result):
                self._uid_accounts[user_id] = result.data['account_user_id']
        return self._uid_accounts.get(user_id)

    def web_checkout_url(self, sn, source=constant.TransactionType.PAYMENT):
        return self._generate_api_url(self.config.WEB_CHECKOUT_URL, source=source, sn=sn)

    def checkout_url(self, sn):
        return self.config.CHECKOUT_URL.format(sn=sn)

    def get_payment_result(self, sn):
        url = self._generate_api_url(self.config.PAYMENT_RESULT_URL, sn=sn)
        return self._do_request(url)

    def get_payment_info(self, sn, payment_scene='_'):
        url = self._generate_api_url(self.config.PAYMENT_INFO_URL, sn=sn, payment_scene=payment_scene)
        return self._do_request(url)

    def get_payment_param(self, sn, payment_scene, vas_name, extra_params=None):
        params = {
            'sn': sn,
            'payment_scene': payment_scene,
            'vas_name': vas_name,
        }

        url = self._generate_api_url(self.config.PAYMENT_PARAM_URL, **params)
        if extra_params:
            url = build_url(url, **extra_params)
        return self._do_request(url)

    def web_payment_callback(self, sn, result):
        params = {
            'sn': sn,
            'result': result
        }
        url = self._generate_api_url(self.config.PAYMENT_CALLBACK_URL)

        params = self._add_sign_to_params(params)
        return submit_form(url, params)

    def zyt_pay(self, sn, payer_user_id):
        params = {
            'sn': sn,
            'payer_user_id': payer_user_id,
        }

        url = self._generate_api_url(self.config.ZYT_PAY_URL)
        result = self.post_req(url, params)
        if is_success_result(result):
            return result.data['is_success']
        return None

    def preprepaid(self, to_user_id, amount, to_domain_name="", callback_url="", notify_url="", order_id=None):
        params = {
            'to_user_id': to_user_id,
            'to_domain_name': to_domain_name,
            'amount': amount,
            'callback_url': callback_url,
            'notify_url': notify_url
        }
        if order_id is not None:
            params['order_id'] = order_id

        url = self._generate_api_url(self.config.PREPREPAID_URL)
        result = self.post_req(url, params)
        if is_success_result(result):
            return result.data['sn']
        return None

    def prepaid_web_checkout_url(self, *args, **kwargs):
        sn = self.preprepaid(*args, **kwargs)
        if sn is not None:
            return self.web_checkout_url(sn, constant.TransactionType.PREPAID)

    def prepay(self, params, ret_sn=False):
        params = dict(params)
        url = self._generate_api_url(self.config.PREPAY_URL)
        result = self.post_req(url, params)
        if is_success_result(result):
            if ret_sn:
                return result.data['sn']
            return result.data['pay_url']
        return None

    def prepay_channel_order(self, order_id, order_channel=None, ret_sn=False):
        params = {
            'order_channel': order_channel or self.config.CHANNEL_NAME,
            'order_id': order_id
        }

        url = self._generate_api_url(self.config.PREPAY_CHANNEL_ORDER_URL, **params)
        result = self.get_req(url, params)
        if is_success_result(result):
            if ret_sn:
                return result.data['sn']
            return result.data['pay_url']
        return None

    def pay_web_checkout_url(self, params):
        sn = self.prepay(params, ret_sn=True)
        if sn is not None:
            return self.web_checkout_url(sn)

    def confirm_guarantee_payment(self, order_id, ret_result=False):
        params = {
            'order_id': order_id
        }

        url = self._generate_api_url(self.config.CONFIRM_GUARANTEE_PAYMENT_URL)
        result = self.post_req(url, params)

        if ret_result:
            return result

        return is_success_result(result)

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

        if is_success_result(result):
            return result.data['sn']
        return None

    def list_transactions(self, user_id, role, page_no, page_size, vas_name, q):
        url = self._generate_api_url(self.config.LIST_USER_TRANSACTIONS_URL, user_id=user_id)

        params = {
            'role': role,
            'page_no': page_no,
            'page_size': page_size
        }
        if q:
            params['q'] = q
        if vas_name:
            params['vas_name'] = vas_name

        url = build_url(url, **params)

        params['user_id'] = user_id
        result = self.get_req(url, params)

        if is_success_result(result):
            return result.data['data']
        return None

    def app_query_bin(self, card_no):
        params = {
            'card_no': card_no
        }
        url = self._generate_api_url(self.config.APP_QUERY_BIN_URL, **params)

        result = self.get_req(url, params)
        if is_success_result(result):
            return result.data['data']
        return None

    def app_bind_bankcard(self, user_id, params=None, ret_result=False):
        params = dict(params)
        params['user_id'] = user_id

        url = self._generate_api_url(self.config.APP_BIND_BANKCARD_URL, user_id=user_id)
        result = self.post_req(url, params)
        if ret_result:
            return result

        if is_success_result(result):
            return result.data['id']
        return None

    def app_unbind_bankcard(self, user_id, bankcard_id):
        params = {
            'user_id': user_id,
            'bankcard_id': bankcard_id
        }

        url = self._generate_api_url(self.config.APP_UNBIND_BANKCARD_URL, **params)
        result = self.post_req(url, params)

        return is_success_result(result)

    def app_get_user_bankcard(self, user_id, bankcard_id):
        params = {'user_id': user_id, 'bankcard_id': bankcard_id}

        url = self._generate_api_url(self.config.APP_GET_USER_BANKCARD_URL, **params)
        result = self.get_req(url, params)

        if is_success_result(result):
            return result.data['data']
        return None

    def app_list_user_bankcards(self, user_id):
        params = {'user_id': user_id}

        url = self._generate_api_url(self.config.APP_LIST_USER_BANKCARDS_URL, **params)
        result = self.get_req(url, params)

        if is_success_result(result):
            return result.data['data']
        return None

    def app_withdraw(self, user_id, bankcard_id=None, amount=None, notify_url=None, order_id=None,
                     params=None, ret_result=False):
        if params is None:
            params = {
                'user_id': user_id,
                'bankcard_id': bankcard_id,
                'amount': amount,
                'notify_url': notify_url
            }
            if order_id is not None:
                params['order_id'] = order_id
        else:
            params = dict(params)
            params['user_id'] = user_id

        url = self._generate_api_url(self.config.APP_WITHDRAW_URL, user_id=user_id)
        result = self.post_req(url, params)
        if ret_result:
            return result

        if is_success_result(result):
            return result.data
        return None

    def app_query_withdraw(self, user_id, sn, ret_result=False):
        params = {
            'user_id': user_id,
            'sn': sn
        }

        url = self._generate_api_url(self.config.APP_QUERY_WITHDRAW_URL, **params)
        result = self.get_req(url, params)
        if ret_result:
            return result

        if is_success_result(result):
            return result.data['data']
        return None

    def app_query_user_balance(self, user_id):
        params = {
            'user_id': user_id
        }
        url = self._generate_api_url(self.config.APP_QUERY_USER_BALANCE_URL, **params)
        result = self.get_req(url, params)

        if is_success_result(result):
            logger.info("balance: {0} => {1}".format(user_id, result.data['data']))
            return result.data['data']
        return {'total': Decimal(0), 'available': Decimal(0), 'frozen': Decimal(0)}

    def app_query_user_available_balance(self, user_id):
        return self.app_query_user_balance(user_id)['available']

    @which_to_return
    def app_draw_cheque(self, user_id, params):
        params['user_id'] = user_id

        url = self._generate_api_url(self.config.APP_DRAW_CHEQUE_URL, user_id=user_id)
        return self.post_req(url, params)

    @which_to_return
    def app_cash_cheque(self, user_id, cash_token):
        params = {
            'user_id': user_id,
            'cash_token': cash_token
        }

        url = self._generate_api_url(self.config.APP_CASH_CHEQUE_URL, **params)
        return self.post_req(url, params)

    @which_to_return
    def app_cancel_cheque(self, user_id, sn):
        params = {
            'user_id': user_id,
            'sn': sn
        }

        url = self._generate_api_url(self.config.APP_CANCEL_CHEQUE_URL, user_id=user_id)
        return self.post_req(url, params)

    @which_to_return
    def app_list_cheque(self, user_id):
        params = {
            'user_id': user_id
        }

        url = self._generate_api_url(self.config.APP_LIST_CHEQUE_URL, user_id=user_id)
        return self.get_req(url, params=params)

    @which_to_return
    def user_transfer(self, user_id, to_user_domain_name, to_user_id, amount, info='', order_id=''):
        params = {
            'user_id': user_id,
            'to_user_domain_name': to_user_domain_name,
            'to_user_id': to_user_id,
            'amount': amount,
            'info': info,
            'order_id': order_id
        }

        url = self._generate_api_url(self.config.USER_TRANSFER_URL, **params)
        return self.post_req(url, params)
