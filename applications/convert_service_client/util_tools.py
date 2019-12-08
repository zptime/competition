#!/usr/bin/env python
# coding=utf-8

import json
import datetime
import urllib2
import urllib
import logging

from urlparse import urlparse
from django.conf import settings

from utils.constant import REQUEST_CONNECTION_TIMEOUT_SECONDS

logger = logging.getLogger(__name__)

# 标志位
FLAG_YES = 1
FLAG_NO = 0

# error code
ERR_SUCCESS = [0, u'完成']
ERR_REQUESTWAY = [40006, u'请求方式错误']
ERR_MODEL_NAME_ERR = [40025, u"模块名称不存在"]
ERR_LOGIN_FAIL = [40003, u'用户名或密码错误']
ERR_USER_NOTLOGGED = [40004, u'用户未登录']
ERR_USER_AUTH = [40005, u'用户权限不够']
ERR_ITEM_NOT_EXIST = [40007, u'记录不存在']

# 用户类型
USER_TYPE_STUDENT = 1
USER_TYPE_TEACHER = 2
USER_TYPE_PARENT = 4

# 时间格式
DATE_FORMAT_MONTH = 2
DATE_FORMAT_DAY = 3
DATE_FORMAT_TIME = 4
SECONDS_PER_DAY = 24*60*60

# 是否检查登录
IS_CHECK_LOGIN = True


# 科目/章节
ERR_SUBJECT_HAVE_EXIST_ERROR = [40060, u'科目已经存在']
ERR_SUBJECT_ID_ERROR = [40061, u'科目ID不正确']
ERR_SUBJECT_GRADE_NUM_ERROR = [40062, u'科目的年级设置不正确']
ERR_TEXTBOOK_HAVE_EXIST_ERROR = [40063, u'教材已经存在']
ERR_TEXTBOOK_ID_ERROR = [40064, u'教材ID不正确']
ERR_CHAPTER_ID_ERROR = [40065, u'章节ID不正确']


def auth_check(request, method="POST", check_login=True):
    dictResp = {}

    log_request(request)
    if not IS_CHECK_LOGIN:
        return dictResp

    if check_login:
        if not request.user.is_authenticated():
            dictResp = {'c': ERR_USER_NOTLOGGED[0], 'e': ERR_USER_NOTLOGGED[1]}
            return dictResp
    if request.method != method.upper():
        dictResp = {'c': ERR_REQUESTWAY[0], 'e': ERR_REQUESTWAY[1]}
        return dictResp

    return dictResp


def log_request(request):
    # self.start_time = time.time()
    remote_addr = request.META.get('REMOTE_ADDR')
    if remote_addr in getattr(settings, 'INTERNAL_IPS', []):
        remote_addr = request.META.get('HTTP_X_FORWARDED_FOR') or remote_addr
    if hasattr(request, 'user'):
        user_account = getattr(request.user, 'username', '-')
    else:
        user_account = 'nobody-user'
    if 'POST' == str(request.method):
        logger.info('[POST] %s %s %s :' % (remote_addr, user_account, request.get_full_path()))
        # info(request.POST)
    if 'GET' == str(request.method):
        logger.info('[GET] %s %s %s :' % (remote_addr, user_account, request.get_full_path()))
        # info(request.GET)


# 请求第三方网站数据
def send_http_request(url, method="POST", form_data_dict=None):
    handler = urllib2.HTTPHandler()
    opener = urllib2.build_opener(handler)

    # build a request
    data = urllib.urlencode(form_data_dict)
    request = urllib2.Request(url, data=data)

    # add any other information you want
    request.add_header("Content-Type", 'application/x-www-form-urlencoded')
    # overload the get method function with a small anonymous function...
    request.get_method = lambda: method

    try:
        connection = opener.open(request, timeout=REQUEST_CONNECTION_TIMEOUT_SECONDS)
    except urllib2.HTTPError, e:
        # connection = e
        logger.error("Request ERROR url: %s method: %s form_data_dict: %s" % (url, method, str(form_data_dict)))
        raise Exception(u"无法连接到网站")

    # check. Substitute with appropriate HTTP code.
    if connection.code == 200:
        data = connection.read()
        return data
    else:
        # handle the error case. connection.read() will still contain data
        # if any was returned, but it probably won't be of any use
        logger.error("Request ERROR response_code: %s url: %s method: %s form_data_dict: %s" % (str(connection.code),
                                                                                                url, method,
                                                                                                str(form_data_dict)))
        raise Exception(u"请求网站返回值不是200")


class RoundTripEncoder(json.JSONEncoder):
    DATE_FORMAT = "%Y-%m-%d"
    TIME_FORMAT = "%H:%M:%S"

    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return {
                "_type": "datetime",
                "value": obj.strftime("%s %s" % (
                    self.DATE_FORMAT, self.TIME_FORMAT
                ))
            }
        return super(RoundTripEncoder, self).default(obj)


class RoundTripDecoder(json.JSONDecoder):
    def __init__(self, *args, **kwargs):
        json.JSONDecoder.__init__(self, object_hook=self.object_hook, *args, **kwargs)

    def object_hook(self, obj):
        if '_type' not in obj:
            return obj
        type = obj['_type']
        if type == 'datetime':
            return datetime.datetime.strptime(obj['value'], '%Y-%m-%d %H:%M:%S')
        return obj


def convert_datetime_to_str(date, date_format=DATE_FORMAT_DAY):
    try:
        date_str = date.strftime('%Y-%m-%d')
        if date_format == DATE_FORMAT_MONTH:
            date_str = date.strftime('%Y-%m')
        elif date_format == DATE_FORMAT_TIME:
            date_str = date.strftime('%Y-%m-%d %H:%M:%S')
        return date_str
    except Exception as ex:
        # logger.warn("datetime_to_str fail")
        return ""


def get_domain_name(url):
    parsed_uri = urlparse(url)
    domain = '{uri.scheme}://{uri.netloc}'.format(uri=parsed_uri)
    return domain
