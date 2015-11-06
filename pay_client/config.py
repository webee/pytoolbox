# coding=utf-8


class Config:
    MD5_KEY = ''
    CHANNEL_PRI_KEY = ''
    # sample
    CHANNEL_NAME = 'zyt_sample'

    ROOT_URL = "http://pay.lvye.com/api/__"
    QUERY_USER_IS_OPENED_URL = "/user_mapping/users/{user_id}/is_opened"
    PREPAY_URL = '/biz/prepay'
    CONFIRM_GUARANTEE_PAYMENT_URL = '/biz/pay/guarantee_payment/confirm'
    REFUND_URL = '/biz/refund'
    WITHDRAW_URL = '/biz/users/{user_id}/withdraw'
    QUERY_WITHDRAW_URL = '/biz/users/{user_id}/withdraw/{sn}'
    APP_WITHDRAW_URL = '/application/users/{user_id}/withdraw'
    APP_QUERY_BIN_URL = '/application/bankcard/{card_no}/bin'
    APP_BIND_BANKCARD_URL = '/application/users/{user_id}/bankcards/bind'
    APP_UNBIND_BANKCARD_URL = '/application/users/{user_id}/bankcards/{bankcard_id}/unbind'
    APP_GET_USER_BANKCARD_URL = '/application/users/{user_id}/bankcards/{bankcard_id}'
    APP_LIST_USER_BANKCARDS_URL = '/application/users/{user_id}/bankcards'
    APP_QUERY_USER_BALANCE_URL = "/application/users/{user_id}/balance"

    PREPREPAID_URL = '/biz/preprepaid'

    PAYMENT_RESULT_URL = '/biz/payment/{sn}/result'
    PAYMENT_INFO_URL = '/biz/payment/{sn}/{payment_scene}/info'
    PAYMENT_PARAM_URL = '/biz/payment/{sn}/{payment_scene}/{vas_name}/param'
    CHECKOUT_URL = 'http://pay.lvye.com/checkout/{sn}'
    WEB_CHECKOUT_URL = '/checkout/web/{source}/{sn}'
    WEB_ZYT_PAY_URL = '/checkout/web/pay/zyt/{sn}'

    GET_ACCOUNT_USER_URL = '/user_mapping/users/{user_id}'
    GET_CREATE_ACCOUNT_USER_URL = '/user_mapping/users/{user_id}'

    LIST_USER_TRANSACTIONS_URL = "/biz/users/{user_id}/transactions"
