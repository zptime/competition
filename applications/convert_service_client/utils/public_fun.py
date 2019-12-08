#!/usr/bin/python
# -*- coding: utf-8 -*-
import urllib2
import urllib
import base64
import hmac
import hashlib
import datetime
import logging
from django.conf import settings

# from ..conf import CONVERT_SERVICE_CLIENT_APP_URL_CONF, CONVERT_SERVICE_SERVER_URL_CONF
from ...upload_resumable.storage.storage import get_storage_obj
from constant import *
from wsgiref.util import FileWrapper
from django.http import HttpResponse
from err_code import *
import os
import requests
from urlparse import urlparse
# from ....utils.public_fun import get_file_url, get_file_type
if settings.CONVERT_SERVICE_CLIENT_APP_URL_CONF and settings.CONVERT_SERVICE_SERVER_URL_CONF:
    pass
else:
    from ..user_center.agents import get_service_url


logger = logging.getLogger(__name__)


def gen_signature(key):
    now = datetime.datetime.now()
    timestamp = now.strftime('%Y-%m-%d %H:%M:%S')
    h = hmac.new(key=key, msg=timestamp, digestmod=hashlib.sha256)
    signature = base64.encodestring(h.digest()).strip()
    return timestamp, signature


# 请求第三方网站数据
def send_http_request(url, method="POST", form_data_dict=None):
    handler = urllib2.HTTPHandler()
    opener = urllib2.build_opener(handler)

    # build a request
    data = None
    if form_data_dict:
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
        raise Exception(u"无法连接到网站")

    # check. Substitute with appropriate HTTP code.
    if connection.code == 200:
        data = connection.read()
        return data
    else:
        # handle the error case. connection.read() will still contain data
        # if any was returned, but it probably won't be of any use
        raise Exception(u"请求网站返回值不是200")


def string_is_null(s):
    if s is None or len(s.strip())==0:
        return True
    else:
        return False


def xor_crypt_string(data, key=settings.PASSWORD_CRYPT_KEY, encode=False, decode=False):
    from itertools import izip, cycle
    import base64
    if decode:
        data = base64.decodestring(data)
    xored = ''.join(chr(ord(x) ^ ord(y)) for (x,y) in izip(data, cycle(key)))
    if encode:
        return base64.encodestring(xored).strip()
    return xored


def str_to_datetime(date_str, is_end=False):
    date_format = DATE_FORMAT_DAY
    try:
        date_list = date_str.split('-')
        if len(date_list) < 0:
            return None
        year = int(date_list[0])
        month = int(date_list[1])
        if len(date_list) == 3:
            day = int(date_list[2])
        elif len(date_list) == 2:
            day = 1
            date_format = DATE_FORMAT_MONTH
        else:
            raise Exception("只支持【年月】和【年月日】两种日期格式")

        date = datetime.datetime(year, month, day)

        if is_end:
            if date_format == DATE_FORMAT_DAY:
                date = date + datetime.timedelta(seconds=SECONDS_PER_DAY-1)
            else:
                raise Exception("只支持【年月日】作为过滤条件查询")
        return date
    except Exception as ex:
        logger.exception(ex.message)
        raise Exception("日期格式转换失败")


def str_p_datetime(datetime_str, str_format='%Y-%m-%d %H:%M:%S'):
    try:
        date_time = datetime.datetime.strptime(datetime_str, str_format)
        return date_time
    except Exception as ex:
        logger.exception(ex.message)
        raise Exception(u"日期时间格式[%s]转换失败" % unicode(str_format, encoding='utf-8'))


def datetime_f_str(date_time, str_format='%Y-%m-%d %H:%M:%S'):
    if isinstance(date_time, datetime.datetime):
        datetime_str = date_time.strftime(str_format)
        return datetime_str
    else:
        raise Exception(u"datetime_to_str fail")


def datetime_to_str(date, include_day=True):
    try:
        # date = timezone.localtime(date)
        if include_day:
            date_str = date.strftime('%Y-%m-%d')
        else:
            date_str = date.strftime('%Y-%m')
        return date_str
    except Exception as ex:
        # logger.warn("datetime_to_str fail")
        return ""


def str_to_int(s):
    try:
        return int(s)
    except Exception as ex:
        # logger.warn("str_to_int fail")
        return -1


def gen_file_reponse(file_path):
    wrapper = FileWrapper(open(file_path, 'rb'))
    response = HttpResponse(wrapper, content_type='application/vnd.ms-excel')
    response['Content-Length'] = os.path.getsize(file_path)
    response['Content-Encoding'] = 'utf-8'
    response['Content-Disposition'] = 'attachment;filename=%s' % os.path.basename(file_path)
    return response


# 输入参数
# rows: 每页最大行数
# page: 请求第几页从1开始计数
# sidx: 排序的列名
# sord: 升序或降序（asc:升序）

# 输出参数
# total: 总页数
# page: 当前第几页
# records: 总记录数（行数）
# items: 请求数据元素列表

def paging(item_list, rows, page, sidx="", sord="asc"):
    # 计算记录数量和页数
    ret_items = []
    records = len(item_list)
    total = records/rows
    if records % rows > 0:
        total += 1
    if page > total:
        page = total

    # 排序
    if sidx:
        reverse = False
        if sord != "asc":
            reverse = True
        if item_list and sidx in item_list[0].keys():
            item_list.sort(key=lambda x: x[sidx], reverse=reverse)

    # compute start and end index
    start = (page-1)*rows
    end = start + rows
    if start < 0 or end < start:
        logger.error("error start=%d, end=%d" % (start, end))
    else:
        ret_items = item_list[start:end]

    ret_val = dict(
        total=str(total),
        page=str(page),
        records=str(records),
        items=ret_items,
    )
    return ret_val


def paging_with_request(request, dictResp):
    rows = request.POST.get("rows", "")
    page = request.POST.get("page", "")
    sidx = request.POST.get("sidx", "")
    sord = request.POST.get("sord", "")
    if not rows or not page or dictResp["c"] != ERR_SUCCESS[0]:
        return dictResp
    item_list = dictResp["d"]
    dictResp["d"] = paging(item_list, int(rows), int(page), sidx, sord)
    return dictResp


# 下载文件
def download_file(url, local_dir=settings.TEMP_DIR, file_name=None):
    if not file_name:
        local_filename = url.split('/')[-1]
        local_path = os.path.join(local_dir, local_filename)
    else:
        local_path = os.path.join(local_dir, file_name)
    # NOTE the stream=True parameter
    r = requests.get(url, stream=True)
    if r.status_code != 200:
            # or r.headers.get('Content-Type') != 'binary/octet-stream':
        logger.error("download file error: %s" % url)
        return ""
    with open(local_path, 'wb') as f:
        for chunk in r.iter_content(chunk_size=1024):
            if chunk:  # filter out keep-alive new chunks
                f.write(chunk)
                f.flush()
    if os.path.exists(local_path):
        return local_path
    else:
        logger.error("download file error: %s" % url)
        return ""


def get_relative_url(url):
    parsed_uri = urlparse(url)
    path = '{uri.path}'.format(uri=parsed_uri)
    return path


def get_file_type(file_name, type_list=SUPPORTED_FILE_TYPE):
    ext = ""
    if len(file_name) < 2:
        return FILE_TYPE_UNKNOWN[0], ext
    ext = os.path.splitext(file_name)[-1].lower()
    for file_type in type_list:
        if ext in file_type[1]:
            return file_type[0], ext
    return FILE_TYPE_UNKNOWN[0], ext


def get_file_url(path, absolute=None, internet=True):
    """
    :param path: 不包含bucket_name或media，保存在FileObj中的url的原始路径
    :param abs: 是否返回包含域名的绝对地址
    :param internet: 是否返回外网地址，否则返回内网地址，abs为True时生效
    :return: 返回文件的url
    """

    url = ""
    if not path:
        return url
    path = get_storage_obj().get_relative_url(path)

    # 不包含该参数时采用系统配置
    if settings.DATA_STORAGE_USE_S3_HOST_URL and settings.DATA_STORAGE_USE_S3:  # 开发环境才使用该配置
        url = 'http://' + settings.AWS_S3_HOST + ":" + str(settings.AWS_S3_PORT) + path
    elif absolute and not internet and settings.DATA_STORAGE_USE_S3:  # 采用S3存储，获取内网下载地址
        url = 'http://' + settings.AWS_S3_HOST + ":" + str(settings.AWS_S3_PORT) + path
    elif absolute or (absolute is None and settings.DATA_STORAGE_USE_ABSOLUTE_URL):
        url = get_service_url(settings.SELF_APP, internet) + path
    else:
        url = path
    return url
