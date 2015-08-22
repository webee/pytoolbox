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
    def __init__(self, md5_key=None, pri_key=None, pub_key=None):
        self.md5_key = md5_key
        self.pri_key = pri_key
        self.pub_key = pub_key

    def init(self, md5_key, pri_key, pub_key):
        self.md5_key = md5_key
        self.pri_key = pri_key
        self.pub_key = pub_key

    def md5_sign(self, data):
        return _sign_md5_data(data, self.md5_key)

    def rsa_sign(self, data):
        return _sign_rsa_data(data, self.pri_key)

    def sign(self, data, sign_type):
        if sign_type == SignType.MD5:
            return _sign_md5_data(data, self.md5_key)
        elif sign_type == SignType.RSA:
            return _sign_rsa_data(data, self.pri_key)
        raise UnknownSignTypeError(sign_type)

    def verify(self, data, sign_type):
        if sign_type == SignType.MD5:
            return _verify_md5_data(data, self.md5_key)
        elif sign_type == SignType.RSA:
            return _verify_rsa_data(data, self.pub_key)
        raise UnknownSignTypeError(sign_type)


def _gen_sign_data(data):
    keys = data.keys()
    keys.sort(key=lambda x: x.lower())

    values = ['%s=%s' % (k, data[k]) for k in keys if k and k != 'sign' and data[k]]

    return '&'.join(values)


def _sign_md5(src, key):
    src = src + '&key=' + key
    src = src.encode('utf-8')
    return md5(src).hexdigest()


def _sign_md5_data(data, key):
    src = _gen_sign_data(data)
    return _sign_md5(src, key)


def _verify_md5(src, key, signed):
    return signed == _sign_md5(src, key)


def _verify_md5_data(data, key):
    signed = data.get('sign')
    src = _gen_sign_data(data)

    return _verify_md5(src, key, signed)


def _sign_rsa(src, pri_key):
    """ 私钥签名
    :param src: 数据字符串
    :param pri_key: 私钥
    :return:
    """
    key = public_key.loads_b64encoded_key(pri_key)
    src = src.encode('utf-8')
    return key.sign_md5_to_base64(src)


def _sign_rsa_data(data, pri_key):
    src = _gen_sign_data(data)

    return _sign_rsa(src, pri_key)


def _verify_rsa(src, pub_key, signed):
    """ 公钥验签
    :param src: 数据字符串
    :param pub_key: 公钥
    :return:
    """
    key = public_key.loads_b64encoded_key(pub_key)
    return key.verify_md5_from_base64(src.encode('utf-8'), signed)


def _verify_rsa_data(data, pub_key):
    signed = data.get('sign')
    src = _gen_sign_data(data)

    return _verify_rsa(src, pub_key, signed)
