# coding=utf-8
from Crypto import Random
from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5
from Crypto.Hash import SHA, MD5, SHA256
from Crypto.Cipher import PKCS1_OAEP
import base64


class Key(object):
    def __init__(self, rsa_key):
        self._key = rsa_key
        self._signer = PKCS1_v1_5.new(self._key)
        self._cipher = PKCS1_OAEP.new(self._key, hashAlgo=SHA256)

    def gen_public_key(self):
        """如果此含私钥，则生成相应的公钥
        """
        if self.has_private():
            return Key(self._key.publickey())

    def has_private(self):
        """是否含私钥
        :return:
        """
        return self._key.has_private()

    def key_data(self, format='PEM', pkcs=1):
        """如果此含私钥，则返回私钥内容;
        否则返回公钥内容
        :return:
        """
        return self._key.exportKey(format, pkcs=pkcs)

    def b64encoded_binary_key_data(self):
        """对于private key生成PKCS#8 DER SEQUENCE
        对于public key生成X.509 DER SEQUENCE
        """
        return base64.b64encode(self.key_data(format='DER', pkcs=8))

    def export(self, fout):
        """导出key_data到fout
        :param fout:
        :return:
        """
        fout.write(self.key_data())

    def sign_sha(self, data):
        h = SHA.new()
        h.update(data)

        return self._signer.sign(h)

    def sign_sha_to_base64(self, data, urlsafe=False):
        if urlsafe:
            return base64.urlsafe_b64encode(self.sign_sha(data))
        return base64.b64encode(self.sign_sha(data))

    def verify_sha(self, data, signature):
        h = SHA.new()
        h.update(data)

        return self._signer.verify(h, signature)

    def verify_sha_from_base64(self, data, signature, urlsafe=False):
        if urlsafe:
            return self.verify_sha(data, base64.urlsafe_b64decode(signature))
        return self.verify_sha(data, base64.b64decode(signature))

    def sign_md5(self, data):
        """对数据先进行md5 hash，再用私钥签名"""
        h = MD5.new()
        h.update(data)

        return self._signer.sign(h)

    def sign_md5_to_base64(self, data, urlsafe=False):
        """对数据先进行md5 hash，再用私钥签名, 并用base64编码结果"""
        if urlsafe:
            return base64.urlsafe_b64encode(self.sign_md5(data))
        return base64.b64encode(self.sign_md5(data))

    def verify_md5(self, data, signature):
        """用公钥验签"""
        h = MD5.new()
        h.update(data)

        return self._signer.verify(h, signature)

    def verify_md5_from_base64(self, data, signature, urlsafe=False):
        """用公钥验签进base64编码的签名"""
        if urlsafe:
            return self.verify_md5(data, base64.urlsafe_b64decode(signature))
        return self.verify_md5(data, base64.b64decode(signature))

    def encrypt(self, data):
        """使用公钥加密数据"""
        return self._cipher.encrypt(data)

    def encrypt_to_base64(self, data):
        """使用公钥加密数据并用base64编码结果"""
        return base64.b64encode(self.encrypt(data))

    def decrypt(self, ciphertext):
        """使用私钥解密密文"""
        return self._cipher.decrypt(ciphertext)

    def decrypt_from_base64(self, ciphertext):
        """使用私钥解密经base64编码的密文"""
        return self._cipher.decrypt(base64.b64decode(ciphertext))


def generate_key(bits=2048):
    rng = Random.new().read

    return Key(RSA.generate(bits, rng))


def load_key(key_path):
    return Key(RSA.importKey(open(key_path).read()))


def loads_key(key_data):
    return Key(RSA.importKey(key_data))


def load_b64encoded_key(key_path):
    return Key(RSA.importKey(base64.b64decode(open(key_path).read())))


def loads_b64encoded_key(encoded_key_data):
    return loads_key(base64.b64decode(encoded_key_data))
