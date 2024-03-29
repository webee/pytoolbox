# coding=utf-8
from __future__ import unicode_literals
from hashlib import md5
from . import public_key


class UnknownSignTypeError(Exception):
    def __init__(self, sign_type):
        message = "Unknown sign type [{0}].".format(sign_type)
        super(UnknownSignTypeError, self).__init__(message)


class SignType:
    MD5 = 'MD5'
    RSA = 'RSA'


class RSASignType:
    SHA = 'SHA'
    MD5 = 'MD5'


class Signer(object):
    def __init__(self, md5_key_param_name='key', sign_key_name='sign', md5_key=None, pri_key=None, pub_key=None,
                 is_inner_key='_is_inner', ignore_case=True, use_uppercase=False,
                 ignore_keys=set(), include_keys=set()):
        """
        :param md5_key_param_name: md5_key本身是要参与签名的，此为生成原始字符串时其参数名
        :param sign_key_name: 签名参数名
        :param md5_key:
        :param pri_key:
        :param pub_key:
        :param is_inner_key: is_inner表示是否为相同的私钥签名的，is_inner_key为此值的参数名
        :param ignore_case: 在生成签名串时是否忽略大小写
        :param use_uppercase: md5最后的sign是否转化成大写
        :return:
        """
        self.md5_key_param_name = md5_key_param_name
        self.sign_key_name = sign_key_name
        self.md5_key = md5_key
        self.pri_key = pri_key
        self.pri_key_obj = public_key.loads_b64encoded_key(pri_key) if pri_key else None
        self.pub_key = pub_key
        self.pub_key_obj = public_key.loads_b64encoded_key(pub_key) if pub_key else None

        self.is_inner_key = is_inner_key
        self.ignore_case = ignore_case
        self.use_uppercase = use_uppercase
        self.ignore_keys = set(ignore_keys)
        self.ignore_keys.add(self.sign_key_name)

        self.include_keys = set(include_keys)

    def init(self, md5_key=None, pri_key=None, pub_key=None):
        self.md5_key = md5_key
        self.pri_key = pri_key
        self.pri_key_obj = public_key.loads_b64encoded_key(pri_key) if pri_key else None
        self.pub_key = pub_key
        self.pub_key_obj = public_key.loads_b64encoded_key(pub_key) if pub_key else None

    def md5_sign(self, data):
        return self._sign_md5_data(data)

    def rsa_sign(self, data, sign_type=RSASignType.MD5, urlsafe=False):
        return self._sign_rsa_data(data, sign_type=sign_type, urlsafe=urlsafe)

    def sign_rsa(self, src, rsa_sign_type=RSASignType.MD5, urlsafe=False):
        return self._sign_rsa(src, self.pri_key_obj, sign_type=rsa_sign_type, urlsafe=urlsafe)

    def sign(self, data, sign_type, rsa_sign_type=RSASignType.MD5, urlsafe=False):
        if sign_type == SignType.MD5:
            return self._sign_md5_data(data)
        elif sign_type == SignType.RSA:
            return self._sign_rsa_data(data, sign_type=rsa_sign_type, urlsafe=urlsafe)
        raise UnknownSignTypeError(sign_type)

    def verify(self, data, sign_type, rsa_sign_type=RSASignType.MD5, urlsafe=False):
        if sign_type == SignType.MD5:
            return self._verify_md5_data(data, self.md5_key)
        elif sign_type == SignType.RSA:
            return self._verify_rsa_data(data, sign_type=rsa_sign_type, urlsafe=urlsafe)
        raise UnknownSignTypeError(sign_type)

    def _sign_md5_data(self, data):
        src = self._gen_sign_data(data)
        return self._sign_md5(src, self.md5_key, self.md5_key_param_name)

    def _verify_md5_data(self, data, key):
        signed = data.get(self.sign_key_name)
        src = self._gen_sign_data(data)

        return self._verify_md5(src, key, signed, self.md5_key_param_name)

    def _sign_rsa_data(self, data, sign_type=RSASignType.MD5, urlsafe=False):
        src = self._gen_sign_data(data)

        return self._sign_rsa(src, self.pri_key_obj, sign_type=sign_type, urlsafe=urlsafe)

    def _verify_rsa_data(self, data, sign_type=RSASignType.MD5, urlsafe=False):
        is_inner = data.get(self.is_inner_key)
        signed = data.get(self.sign_key_name)
        src = self._gen_sign_data(data)

        if not is_inner:
            return self._verify_rsa(src, self.pub_key_obj, signed, sign_type=sign_type, urlsafe=urlsafe)
        # 只要is_inner_key传了，且不为空
        return self._verify_rsa(src, self.pri_key_obj.gen_public_key(), signed, sign_type=sign_type, urlsafe=urlsafe)

    def _is_valid_item(self, k, v):
        return k and k not in self.ignore_keys and (k in self.include_keys or k[0] != '_') \
               and v is not None and v != '' and not isinstance(v, (dict, list))

    def _gen_sign_data(self, data):
        keys = data.keys()
        if self.ignore_case:
            keys.sort(key=lambda x: x.lower())
        else:
            keys.sort()

        # 过滤掉空值，list和dict类型
        values = ['%s=%s' % (k, data[k]) for k in keys if self._is_valid_item(k, data[k])]

        return '&'.join(values)

    def _sign_md5(self, src, key, key_param_name):
        if key_param_name is None:
            src = src + key
        else:
            src = src + '&{0}={1}'.format(key_param_name, key)
        src = src.encode('utf-8')
        s = md5(src).hexdigest()
        if self.use_uppercase:
            return s.upper()
        return s

    def _verify_md5(self, src, key, signed, key_param_name):
        return signed == self._sign_md5(src, key, key_param_name)

    @staticmethod
    def _sign_rsa(src, key, sign_type=RSASignType.MD5, urlsafe=False):
        """ 私钥签名
        :param src: 数据字符串
        :param key: 私钥
        :return:
        """
        src = src.encode('utf-8')
        if sign_type == RSASignType.SHA:
            return key.sign_sha_to_base64(src, urlsafe=urlsafe)
        return key.sign_md5_to_base64(src, urlsafe=urlsafe)

    @staticmethod
    def _verify_rsa(src, key, signed, sign_type=RSASignType.MD5, urlsafe=False):
        """ 公钥验签
        :param src: 数据字符串
        :param key: 公钥
        :return:
        """
        src = src.encode('utf-8')
        if sign_type == RSASignType.SHA:
            return key.verify_sha_from_base64(src, signed, urlsafe=urlsafe)
        return key.verify_md5_from_base64(src, signed, urlsafe=urlsafe)
