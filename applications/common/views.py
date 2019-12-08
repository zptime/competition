# -*- coding=utf-8 -*-

import logging

from django.contrib import auth

from applications.common import services, prjsys
from utils.check_auth import validate
from utils.check_param import InvalidHttpParaException, getp
from utils.const_err import *
from utils.net_helper import response200, response_parameter_error, response_exception
from utils.utils_log import log_request, log_response

logger = logging.getLogger(__name__)


@validate('GET', auth=False)
def api_common_test(request):
    """
    功能说明: 测试函数
    """
    log_request(request)
    try:
        testparam1 = getp(request.GET.get('testparam1'), nullable=False, para_intro='测试参数1')

    except InvalidHttpParaException as ihpe:
        logger.exception(ihpe)
        return response_parameter_error(ihpe)

    try:
        result = services.api_common_test(request, testparam1)
    except Exception as e:
        logger.exception(e)
        return response_exception(e)
    log_response(request, result)
    return response200({'c': SUCCESS[0], 'm': SUCCESS[1], 'd': result})


@validate('GET', auth=False)
def api_common_build_frontapp(request):
    """
    功能说明: 手动编译前端
    """
    log_request(request)
    try:
        yourname = getp(request.GET.get('yourname'), nullable=False, para_intro='编译人')

    except InvalidHttpParaException as ihpe:
        logger.exception(ihpe)
        return response_parameter_error(ihpe)

    try:
        result = prjsys.api_common_build_frontapp(request, yourname)
    except Exception as e:
        logger.exception(e)
        return response_exception(e)
    log_response(request, result)
    return response200({'c': SUCCESS[0], 'm': SUCCESS[1], 'd': result})


@validate('GET', auth=False)
def api_common_build_frontresult(request):
    """
    功能说明: 查看编译结果
    """
    log_request(request)
    try:
        # yourname = getp(request.GET.get('yourname'), nullable=False, para_intro='编译人')
        pass

    except InvalidHttpParaException as ihpe:
        logger.exception(ihpe)
        return response_parameter_error(ihpe)

    try:
        result = prjsys.api_common_build_frontresult(request)
    except Exception as e:
        logger.exception(e)
        return response_exception(e)
    log_response(request, result)
    return response200({'c': SUCCESS[0], 'm': SUCCESS[1], 'd': result})


@validate('GET', auth=False)
def api_common_build_unlock(request):
    """
    功能说明: 解决编译锁定
    """
    log_request(request)
    try:
        # yourname = getp(request.GET.get('yourname'), nullable=False, para_intro='编译人')
        pass

    except InvalidHttpParaException as ihpe:
        logger.exception(ihpe)
        return response_parameter_error(ihpe)

    try:
        result = prjsys.api_common_build_unlock(request)
    except Exception as e:
        logger.exception(e)
        return response_exception(e)
    log_response(request, result)
    return response200({'c': SUCCESS[0], 'm': SUCCESS[1], 'd': result})
