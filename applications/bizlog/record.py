# coding=utf-8

import logging
import json
import datetime

from models import OperateLog
from utils import is_qualify
from django.conf import settings

logger = logging.getLogger(__name__)


def save(request, start_time, end_time, response=None, exception=None):
    # 排除不需要记录日志的请求
    if not is_qualify(request.get_full_path(), settings.LOG_CENTER['include'], settings.LOG_CENTER['exclude']):
        return

    oper_log = OperateLog()
    # 记录请求
    try:
        if request.method == 'GET':
            oper_log.request = (str(request.GET.items())).replace("u\'", "\'").decode('unicode-escape').encode('utf8')
        elif request.method == 'POST':
            request_str = ''
            if request.FILES:
                request_str += u'该请求包含文件上传: %s' % request.FILES.get('file').name
            if request.POST.items():
                request_str += (str(request.POST.items())).replace("u\'", "\'").decode('unicode-escape').encode('utf8')
            oper_log.request = request_str
        else:
            oper_log.request = u'不支持请求方法为%s的日志记录' % request.method

        limit = settings.LOG_CENTER.get('request_record_length', -1)
        if limit != -1 and limit != 0:
            oper_log.request = oper_log.request[:limit]
    except Exception as e:
        logger.exception('oper_log.request encode error')

    # 记录UA
    oper_log.ua = request.META.get('HTTP_USER_AGENT', None)

    # 如果是登录用户，记录用户信息
    if hasattr(request, 'user') and request.user.is_authenticated():
        login_user = request.user
        oper_log.account_id = str(login_user.id)
        # if hasattr(login_user, 'school'):
        #     oper_log.user_school_id = str(request.user.school.id)
        # if hasattr(login_user, 'type'):
        #     oper_log.user_type = request.user.type

    # 记录请求头
    oper_log.head = str(request.META)
    limit = settings.LOG_CENTER.get('head_record_length', -1)
    if limit != -1 and limit != 0:
        oper_log.head = oper_log.head[:limit]

    # 记录请求来源IP
    if request.META.has_key('HTTP_X_FORWARDED_FOR'):
        raw_ip = request.META['HTTP_X_FORWARDED_FOR']
    else:
        raw_ip = request.META['REMOTE_ADDR']
    oper_log.ip = raw_ip[:25]

    # 记录请求方法
    oper_log.method = request.method

    # 记录请求开始时间
    oper_log.request_time = start_time

    # 记录请求结束时间
    oper_log.response_time = end_time

    # 记录请求耗时
    oper_log.duration = (end_time - start_time).total_seconds() * 1000 \
            if end_time and start_time and end_time > start_time else 0

    # 记录请求URL
    oper_log.url = request.get_full_path()

    # 当请求抛异常时，记录响应、状态码、C、M
    if exception:
        except_msg = ''
        if hasattr(exception, 'msg'):
            except_msg = exception.msg
        if hasattr(exception, 'message'):
            except_msg = exception.message
        oper_log.response = except_msg
        oper_log.status_code = '500'
        oper_log.c = -1
        oper_log.m = u'服务器内部异常: %s' % except_msg

    # 当有处理结果时，记录响应、状态码、C、M
    elif response:
        try:
            if response['Content-Type'] != 'application/json':
                oper_log.response = response['Content-Type']
            else:
                oper_log.response = str(response).decode('utf8').encode('utf8')

            limit = settings.LOG_CENTER.get('response_record_length', -1)
            if limit != -1 and limit != 0:
                oper_log.response = oper_log.response[:limit]
        except Exception:
            logger.exception('response decode error')
        oper_log.status_code = response.status_code
        try:
            result_dict = json.loads(response.content)
            oper_log.c = result_dict['c']
            oper_log.m = result_dict['m']
        except Exception:
            oper_log.c = -1
            oper_log.m = u'返回非JSON格式'

    # 当服务器处理无任何返回结果时，记录响应、状态码、C、M
    else:
        oper_log.response = u'服务器处理无任何返回'
        oper_log.status_code = ''
        oper_log.c = -1
        oper_log.m = ''

    # DO SAVE
    oper_log.save()


class LogMiddleware(object):
    request_time = None
    response_time = None

    def process_request(self, request):
        self.request_time = datetime.datetime.now()

    def process_response(self, request, response):
        self.response_time = datetime.datetime.now()
        try:
            save(request, self.request_time, self.response_time, response=response)
        except Exception as e:
            logger.exception('failed to save request log into database')
        finally:
            return response

    def process_exception(self, request, exception):
        self.response_time = datetime.datetime.now()
        try:
            save(request, self.request_time, self.response_time, exception=exception)
        except Exception as e:
            logger.exception(e)
            logger.warn('failed to save request log into database')
        finally:
            logger.exception(exception)
            raise exception