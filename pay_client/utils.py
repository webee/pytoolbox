# coding=utf-8
from functools import wraps
from ..util.log import get_logger


logger = get_logger(__name__)


def is_success_result(result):
    if result is None:
        return False
    ret = result.data['ret']
    if not ret:
        logger.warn("failed result: code: {0}, msg: {1}, data: {2}".format(result.data['code'],
                                                                           result.data['msg'], result.data))
    return ret


def submit_form(url, req_params, method='POST'):
    submit_page = '<form id="formName" action="{0}" method="{1}">'.format(url, method)
    for key in req_params:
        submit_page += '''<input type="hidden" name="{0}" value='{1}' />'''.format(key, req_params[key])
    submit_page += '<input type="submit" value="Submit" style="display:none" /></form>'
    submit_page += '<script>document.forms["formName"].submit();</script>'
    return submit_page


def which_to_return(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        ret_result = False
        if 'ret_result' in kwargs:
            ret_result = kwargs.pop('ret_result')
        result = func(*args, **kwargs)
        if ret_result:
            return result

        if is_success_result(result):
            return result.data
        return None
    return wrapper
