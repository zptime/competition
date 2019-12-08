# coding=utf-8

import logging
import os
import json
import requests

from urlparse import urljoin, urlparse
from django.conf import settings
from django.http import HttpResponse

from models import OperateLog
from utils import today, yesterday, datetime2str, is_qualify, yesterday_str

FAIL = (-1, u'失败')
SUCCESS = (0, u'完成')

logger = logging.getLogger(__name__)


ANALYSIS = {
    'TOTAL_REQ':{
        'desc': u'',
        'include': ['*'],
        'exclude': [],
        'qs': OperateLog.objects.filter(request_time__gte=yesterday(), request_time__lt=today()),
        'display': '{LOGON}/{ANONYMOUS}',
    },
    'TOTAL_USER': {
        'desc': u'',
        'include': ['*'],
        'exclude': [],
        'qs': OperateLog.objects.filter(request_time__gte=yesterday(),
                    request_time__lt=today()).values_list("account_id", flat=True).distinct(),
        'display': '{LOGON}',
    },
    'LONG': {
        'desc': u'\n[http长请求 (>%s毫秒)]: \n' % settings.LOG_CENTER['long_request']['threshold'],
        'include': settings.LOG_CENTER['long_request']['report_include'],
        'exclude': settings.LOG_CENTER['long_request']['report_exclude'],
        'qs': OperateLog.objects.filter(request_time__gte=yesterday(),
                    request_time__lt=today(), duration__gte=settings.LOG_CENTER['long_request']['threshold']),
        'display': '{LOGON}/{ANONYMOUS}',
    },
    '200ERR': {
        'desc': u'\n[http请求"200"且包含非0内部状态码(c)响应]: \n',
        'include': ['*'],
        'exclude': [],
        'qs': OperateLog.objects.filter(request_time__gte=yesterday(), request_time__lt=today(), status_code='200').exclude(c=0),
        'display': '{LOGON}/{ANONYMOUS}',
    },
    'NON200': {
        'desc': u'\n[http请求"非200"响应]: \n',
        'include': ['*'],
        'exclude': [],
        'qs': OperateLog.objects.filter(request_time__gte=yesterday(), request_time__lt=today()).exclude(status_code='200'),
        'display': '{LOGON}/{ANONYMOUS}',
    },
    '500': {
        'desc': u'\n[http请求"500"响应]: \n',
        'include': ['*'],
        'exclude': [],
        'qs': OperateLog.objects.filter(request_time__gte=yesterday(), request_time__lt=today(), status_code='500'),
        'display': '{LOGON}/{ANONYMOUS}',
    },
}


def request_analysis(item, report=None):
    desc = ANALYSIS[item]['desc']
    include = ANALYSIS[item]['include']
    exclude = ANALYSIS[item]['exclude']
    qs = ANALYSIS[item]['qs']
    display = ANALYSIS[item]['display']

    data_list_all = [each for each in qs if is_qualify(each.url, include, exclude)]
    data_list_logon = [each for each in qs.exclude(account_id=None) if is_qualify(each.url, include, exclude)]

    if report:
        lines = list()
        report.writelines([desc, ])
        for each in data_list_all:
            requester = 'anonymous'
            if each.account_id:
                requester = str(each.account_id)
            if each.account_id and each.user_type and each.user_school_id:
                requester = '%d_%d_%d' % (each.account_id, each.user_type, each.user_school_id)
            lines.append(u'ID:%d, URL:%s, 时长:%d, 请求者:%s, 响应码:%s, c:%s, m:%s, 时间:%s\n'
                            % (each.id, each.url, each.duration, requester, each.status_code,
                               each.c, each.m, datetime2str(each.request_time)))
        report.writelines(lines)

    fill_map = {
        'LOGON' : len(data_list_logon),
        'ANONYMOUS': len(data_list_all) - len(data_list_logon),
    }
    return display.format(**fill_map)


def report_log_error(report_file):
    # django日志文件中ERROR个数
    def _report_single_log_error(log_path, report_file):
        inner_count = 0
        yesterday_string = yesterday_str()
        with open(log_path, 'r') as f:
            err_bucket = list()
            err_flag = False
            for line in f:
                if line.startswith(yesterday_string):
                    if err_flag:
                        report_file.writelines(err_bucket)
                        err_flag = False
                        err_bucket[:] = []
                    if '[ERROR]' in line:
                        inner_count += 1
                        err_flag = True
                        err_bucket.append(line)
                else:
                    if err_flag:
                        err_bucket.append(line)
        return inner_count
    count = 0
    report_file.writelines([u'\n[django日志文件中ERROR]: \n',])
    (shortname, extension) = os.path.splitext(get_django_log_path())

    rotate_search = settings.LOG_CENTER.get('rotate_search', 1)

    for i in xrange(rotate_search, 0, -1):
        rotate_name = shortname + '.' + str(i) + extension
        if os.path.exists(rotate_name):
            count += _report_single_log_error(rotate_name, report_file)

    count += _report_single_log_error(get_django_log_path(), report_file)
    return count


def get_django_log_path():
    # 查询日志目录，先找LOGGING的配置,找不到则取settings.LOG_CENTER，如果仍找不到，则默认取log/django.log
    try:
        logpath = settings.LOGGING['handlers']['default']['filename']
    except:
        if 'log' in settings.LOG_CENTER:
            logpath = settings.LOG_CENTER['log']
        else:
            logpath = os.path.join(settings.BASE_DIR + '/log/', 'django.log')
    return logpath


def load_appendix(appendix_list):
    result_list = []
    for each in appendix_list:
        if not each:
            continue
        mdl_str = each[: each.rfind('.')]
        func_str = each[each.rfind('.') + 1:]
        mdl = __import__(mdl_str, fromlist=True)
        func = getattr(mdl, func_str)
        result_list.append(func())
    return result_list


def daily_report():
    report_path = os.path.join(settings.TEMP_DIR,
        'report_%s_%s.log' % (yesterday_str(), getattr(settings, 'SYSTEM_DESC', settings.LOG_CENTER.get('system_name', u'未定义'))))

    with open(report_path, 'w+') as report:
        # 前一天总用户数
        user_distinct = request_analysis('TOTAL_USER')

        # 前一天总http请求数
        req_total = request_analysis('TOTAL_REQ')

        # http请求非200响应
        req_non_200 = request_analysis('NON200', report)

        # http请求500响应
        req_500 = request_analysis('500', report)

        # http请求"200"且包含非0内部状态码
        req_200_error = request_analysis('200ERR', report)

        # http长请求
        req_long = request_analysis('LONG', report)

        # 日志中异常ERROR数量
        error_count = report_log_error(report)

    desc1, desc2 = load_appendix([settings.LOG_CENTER['appendix1_func'], settings.LOG_CENTER['appendix2_func']])

    try:
        upload(report_path, user_distinct, req_total, -1,
               req_non_200, req_500, req_200_error, req_long, error_count, desc1, desc2, yesterday_str())
    except Exception as e:
        logger.exception('send log collection info to log center fail')


def upload(report_path, user_count, req_total, req_unsafe, req_non_200, req_500, req_200_error, req_long, error, desc1, desc2, cycle_time):
    """
        上报日志
    """
    payload = {
        'pkg_name': 'applications.mail.services',
        'function_name': 'api_upload_log',
        'parameter': json.dumps({
            'system_code': getattr(settings, 'SYSTEM_NAME', settings.LOG_CENTER.get('system_code', 'none')),
            'system_name': getattr(settings, 'SYSTEM_DESC', settings.LOG_CENTER.get('system_name', u'未定义')),
            'total_user': user_count,
            'total_request': req_total,
            'total_request_unsafe': req_unsafe,
            'request_non_200': req_non_200,
            'request_500': req_500,
            'request_200_with_error': req_200_error,
            'request_long': req_long,
            'report_log_error': error,
            'desription1': desc1,
            'desription2': desc2,
            'cycle_time': cycle_time,
            # 'logfile': report_path,  # report_path
        }, ensure_ascii=False)
    }

    files = {'file_in': open(report_path, 'rb')}

    try:
        logger.info('upload log to log-center:')
        logger.info(str(payload).decode("unicode-escape"))
        remote_response = _remote_call(payload, files)
    except Exception as e:
        logger.exception(e)
        result = {'c': FAIL[0], 'm': FAIL[1], 'd': u'上报日志到日志管理中心失败'}
        return HttpResponse(json.dumps(result, ensure_ascii=False), content_type='application/json')
    logger.info(str(remote_response).decode("unicode-escape"))
    return remote_response


def _remote_call(payload, files=None):
    if files:
        response = requests.post(
            urljoin(settings.LOG_CENTER['domain'], '/api/internal/proxy'),
            data=payload,
            files=files,
            timeout=60)
    else:
        response = requests.post(
            urljoin(settings.LOG_CENTER['domain'], '/api/internal/proxy'),
            data=payload,
            timeout=10)
    return json.loads(response.text)

