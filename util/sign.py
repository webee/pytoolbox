# coding=utf-8
from __future__ import unicode_literals
from hashlib import md5
from pytoolbox.util import public_key


class UnknownSignTypeError(Exception):
    def __init__(self, sign_type):
        message = "Unknown sign type [{0}].".format(sign_type)
        super(UnknownSignTypeError, self).__init__(message)


class SignType:
    MD5 = 'MD5'
    RSA = 'RSA'


class Signer(object):
    def __init__(self, md5_key_param_name='key', sign_key_name='sign', md5_key=None, pri_key=None, pub_key=None,
                 is_inner_key='_is_inner'):
        self.md5_key_param_name = md5_key_param_name
        self.sign_key_name = sign_key_name
        self.md5_key = md5_key
        self.pri_key = pri_key
        self.pri_key_obj = public_key.loads_b64encoded_key(pri_key) if pri_key else None
        self.pub_key = pub_key
        self.pub_key_obj = public_key.loads_b64encoded_key(pub_key) if pub_key else None

        self.is_inner_key = is_inner_key

    def init(self, md5_key, pri_key, pub_key):
        self.md5_key = md5_key
        self.pri_key = pri_key
        self.pri_key_obj = public_key.loads_b64encoded_key(pri_key) if pri_key else None
        self.pub_key = pub_key
        self.pub_key_obj = public_key.loads_b64encoded_key(pub_key) if pub_key else None

    def md5_sign(self, data):
        return self._sign_md5_data(data)

    def rsa_sign(self, data):
        return self._sign_rsa_data(data)

    def sign(self, data, sign_type):
        if sign_type == SignType.MD5:
            return self._sign_md5_data(data)
        elif sign_type == SignType.RSA:
            return self._sign_rsa_data(data)
        raise UnknownSignTypeError(sign_type)

    def verify(self, data, sign_type):
        if sign_type == SignType.MD5:
            return self._verify_md5_data(data, self.md5_key)
        elif sign_type == SignType.RSA:
            return self._verify_rsa_data(data)
        raise UnknownSignTypeError(sign_type)

    def _sign_md5_data(self, data):
        src = self._gen_sign_data(data)
        return _sign_md5(src, self.md5_key, self.md5_key_param_name)

    def _verify_md5_data(self, data, key):
        signed = data.get(self.sign_key_name)
        src = self._gen_sign_data(data)

        return _verify_md5(src, key, signed, self.md5_key_param_name)

    def _sign_rsa_data(self, data):
        src = self._gen_sign_data(data)

        return _sign_rsa(src, self.pri_key_obj)

    def _verify_rsa_data(self, data):
        is_inner = data.get(self.is_inner_key)
        signed = data.get(self.sign_key_name)
        src = self._gen_sign_data(data)

        if not is_inner:
            return _verify_rsa(src, self.pub_key_obj, signed)
        return _verify_rsa(src, self.pri_key_obj.gen_public_key(), signed)

    def _gen_sign_data(self, data):
        keys = data.keys()
        keys.sort(key=lambda x: x.lower())

        values = ['%s=%s' % (k, data[k]) for k in keys if k and k != self.sign_key_name and k[0] != '_' and data[k] != '']

        return '&'.join(values)


def _sign_md5(src, key, key_param_name):
    src = src + '&{0}={1}'.format(key_param_name, key)
    src = src.encode('utf-8')
    return md5(src).hexdigest()


def _verify_md5(src, key, signed, key_param_name):
    return signed == _sign_md5(src, key, key_param_name)


def _sign_rsa(src, key):
    """ 私钥签名
    :param src: 数据字符串
    :param key: 私钥
    :return:
    """
    src = src.encode('utf-8')
    return key.sign_md5_to_base64(src)


def _verify_rsa(src, key, signed):
    """ 公钥验签
    :param src: 数据字符串
    :param key: 公钥
    :return:
    """
    return key.verify_md5_from_base64(src.encode('utf-8'), signed)
