# coding=utf-8
from functools import wraps
from decimal import Decimal

import os
import requests
from ..util.sign import SignType, Signer
from ..util import pmc_config
from ..util.log import get_logger
from ..util.urls import build_url
from .config import Config


logger = get_logger(__name__)


class PayClient(object):

    def __init__(self):
        self.config = Config()
        self.signer = Signer('key', 'sign')
        self._uid_accounts = {}

    def init_config(self, env_config):
        pmc_config.merge_config(self.config, env_config)
        self.signer.init(self.config.MD5_KEY, self.config.CHANNEL_PRI_KEY, self.config.LVYE_PUB_KEY)

    def verify(self, data, do_not_check=True):
        if do_not_check:
            return True
        sing_type = data.get('sign_type')
        channel_name = data.get('channel_name')
        if channel_name != self.config.CHANNEL_NAME:
            return False

        return self.signer.verify(data, sing_type)

    def verify_request(self, f):
        from flask import request

        @wraps(f)
        def wrapper(*args, **kwargs):
            try:
                data = request.values
                # check perm
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
            return f(*args, **kwargs)
        return wrapper

    def request(self, url, params=None, sign_type=SignType.RSA, method='post'):
        if params is None:
            params = {}

        params['sign_type'] = sign_type
        params['channel_name'] = self.config.CHANNEL_NAME
        params['sign'] = self.signer.sign(params, sign_type)

        req = requests.request(method, url, data=params)
        try:
            if req.status_code != 200:
                logger.warn('bad request result: [{0}]'.format(req.text))
                return None
            data = req.json()
            if self.verify(data):
                return data
        except Exception as e:
            logger.exception(e)
            logger.warn('bad request: {0}, {1}'.format(req.status_code, req.text))
        return None

    def _generate_api_url(self, url, **kwargs):
        url = url.lstrip('/')
        url = os.path.join(self.config.ROOT_URL, url.format(**kwargs))
        logger.info("request url %s" % url)
        return url

    def get_account_user_id(self, user_id, user_domain_name=None):
        if user_id not in self._uid_accounts:
            user_domain_name = user_domain_name or self.config.USER_DOMAIN_NAME
            url = self._generate_api_url(self.config.GET_CREATE_ACCOUNT_ID_URL,
                                         user_domain_name=user_domain_name, user_id=user_id)
            data = self.request(url)
            if data is not None:
                self._uid_accounts[user_id] = data['account_user_id']
        return self._uid_accounts.get(user_id)

    def get_user_balance(self, user_id):
        account_user_id = self.get_account_user_id(user_id)
        url = self._generate_api_url(self.config.GET_USER_BALANCE_URL, account_user_id=account_user_id)

        data = self.request(url, method='get')

        if data is not None:
            return data['data']
        return {'total': Decimal(0), 'available': Decimal(0), 'frozen': Decimal(0)}

    def prepay(self, params):
        url = self._generate_api_url(self.config.PREPAY_URL)
        return self.request(url, params)

    def refund(self, params):
        url = self._generate_api_url(self.config.REFUND_URL)
        return self.request(url, params)

    def withdraw(self, user_id, params):
        account_user_id = self.get_account_user_id(user_id)
        url = self._generate_api_url(self.config.WITHDRAW_URL, account_user_id=account_user_id)
        return self.request(url, params)

    def confirm_guarantee_payment(self, params):
        url = self._generate_api_url(self.config.CONFIRM_GUARANTEE_PAYMENT_URL)
        return self.request(url, params)

    def get_user_available_balance(self, uid):
        return self.get_user_balance(uid)[1]

    def list_user_bankcards(self, uid):
        account_user_id = self.get_account_user_id(uid)
        url = self._generate_api_url(self.config.LIST_USER_BANKCARDS_URL, account_user_id=account_user_id)
        data = self.request(url, method='get')

        if data is not None:
            return data['bankcards']
        return []

    def get_bin(self, card_no):
        url = self._generate_api_url(self.config.QUERY_BIN_URL, card_no=card_no)

        return self.request(url, method='get')

    def query_user_is_opened(self, user_id):
        params = {
            'user_domain_name': self.config.USER_DOMAIN_NAME,
            'user_id': user_id
        }

        url = self._generate_api_url(self.config.QUERY_USER_IS_OPENED_URL, **params)

        return self.request(url, params, method='get')

    def query_transactions(self, uid, role, page_no, page_size, q):
        account_user_id = self.get_account_user_id(uid)
        url = self._generate_api_url(self.config.GET_USER_TRANSACTIONS_URL, account_user_id=account_user_id)

        params = {
            'role': role,
            'page_no': page_no,
            'page_size': page_size
        }
        if q:
            params['q'] = q

        url = build_url(url, **params)
        return self.request(url, method='get')
