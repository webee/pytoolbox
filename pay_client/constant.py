# coding=utf-8
from __future__ import unicode_literals


class VirtualAccountSystemType:
    ZYT = 'ZYT'
    TEST_PAY = 'TEST_PAY'
    LIANLIAN_PAY = 'LIANLIAN_PAY'
    WEIXIN_PAY = 'WEIXIN_PAY'
    ALI_PAY = 'ALI_PAY'


class TransactionType:
    PREPAID = 'PREPAID'
    PAYMENT = 'PAYMENT'
    TRANSFER = 'TRANSFER'
    REFUND = 'REFUND'
    WITHDRAW = 'WITHDRAW'


class RequestClientType:
    WEB = 'WEB'
    WAP = 'WAP'
    IOS = 'IOS'
    ANDROID = 'ANDROID'


class PaymentType:
    DIRECT = 'DIRECT'
    GUARANTEE = 'GUARANTEE'
