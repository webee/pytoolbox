# coding=utf-8


class Config:
    MD5_KEY = ''
    LVYE_PUB_KEY = ''
    CHANNEL_PRI_KEY = ''
    # sample
    CHANNEL_NAME = 'zyt_sample'

    ROOT_URL = "http://pay.lvye.com/api/__"
    QUERY_USER_IS_OPENED_URL = "/user_mapping/users/{user_id}/is_opened"
    PREPAY_URL = '/biz/prepay'
    CONFIRM_GUARANTEE_PAYMENT_URL = '/biz/pay/guarantee_payment/confirm'
    REFUND_URL = '/biz/refund'
    WITHDRAW_URL = '/biz/withdraw'
    APP_WITHDRAW_URL = '/application/withdraw'
    PREPAID_URL = '/biz/prepaid'

    GET_ACCOUNT_USER_URL = '/user_mapping/users/{user_id}'
    GET_CREATE_ACCOUNT_USER_URL = '/user_mapping/users/{user_id}'

    QUERY_BIN_URL = '/application/bankcard/{card_no}/bin'
    QUERY_USER_BALANCE_URL = "/vas/zyt/account_users/{account_user_id}/balance"
    LIST_USER_BANKCARDS_URL = '/application/account_users/{account_user_id}/bankcards'

    GET_USER_TRANSACTIONS_URL = "/biz/account_users/{account_user_id}/transactions"
