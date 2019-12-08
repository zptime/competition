#!/usr/bin/env python
# coding=utf-8
import logging

import services
from utils.check_auth import validate
from utils.utils_log import log_request, log_response
from utils.net_helper import response_exception, response_parameter_error, response200
from utils.check_param import getp, InvalidHttpParaException
from utils.public_fun import paging_with_request
from utils.const_err import *

logger = logging.getLogger(__name__)


@validate("POST")
def api_list_expert_user(request):
    log_request(request)
    try:
        # cur_user_id = getp(request.POST.get("cur_user_id"), u"当前用户的id", nullable=False)
        name = getp(request.POST.get("name"), u"姓名", nullable=True)
        area_id = getp(request.POST.get("area_id"), u"地域id", nullable=True)
        manage_direct = getp(request.POST.get("manage_direct"), u"直属标志", nullable=True)
        is_show_store = getp(request.POST.get("is_show_store"), u"是否在专家库显示", nullable=True)
    except InvalidHttpParaException as ex:
        logger.exception(ex)
        return response_parameter_error(ex)
    try:
        result = services.list_expert_user(request.user, None, name, area_id, manage_direct, is_show_store)
        # result = paging_with_request(request, result)
    except Exception as ex:
        logger.exception(ex)
        return response_exception(ex, ex.message)
    if result['c'] == SUCCESS[0]:
        result = paging_with_request(request, result)
    log_response(request, result)
    return response200(result)


@validate("POST")
def api_add_expert_user(request):
    """
    添加专家用户。一般此接口只有其它接口调用，前端不会直接调用。
    当前逻辑为任何用户可以随意添加专家，也可以添加任意地区的专家。
    :param request:
    :return:
    """
    log_request(request)
    try:
        # cur_user_id = getp(request.POST.get("cur_user_id"), u"当前用户id")
        username = getp(request.POST.get("username"), u"用户名")
        name = getp(request.POST.get("name"), u"姓名")
        sex = getp(request.POST.get("sex"), u"性别")
        # area_name = getp(request.POST.get("area_name"), u"地域名称", nullable=True)
        institution = getp(request.POST.get("institution"), u"组织名称", nullable=True)
        # manage_direct = getp(request.POST.get("manage_direct"), u"直属标志", nullable=True)
        area_id = getp(request.POST.get("area_id"), u"区域ID", nullable=True)
        direct_area_id = getp(request.POST.get("direct_area_id"), u"哪一个区域直属", nullable=True)

        image_id = getp(request.POST.get("image_id", ""), u"头像图片", nullable=True)
        position = getp(request.POST.get("position", ""), u"职位信息", nullable=True)
        introduction = getp(request.POST.get("introduction", ""), u"个人介绍", nullable=True)

    except InvalidHttpParaException as ex:
        logger.exception(ex)
        return response_parameter_error(ex)
    try:
        result = services.add_expert_user(request.user, username, name, sex, institution,
                                          image_id, position, introduction, area_id, direct_area_id)
    except Exception as ex:
        logger.exception(ex)
        return response_exception(ex, ex.message)
    log_response(request, result)
    return response200(result)


@validate("POST")
def api_mod_expert_user(request):
    log_request(request)
    try:
        expert_id = getp(request.POST.get("expert_id"), u"专家ID")
        # cur_user_id = getp(request.POST.get("cur_user_id"), u"当前用户id")
        username = getp(request.POST.get("username"), u"用户名")
        name = getp(request.POST.get("name"), u"姓名")
        sex = getp(request.POST.get("sex"), u"性别")
        # area_name = getp(request.POST.get("area_name"), u"地域名称", nullable=True)
        institution = getp(request.POST.get("institution"), u"组织名称", nullable=True)
        # manage_direct = getp(request.POST.get("manage_direct"), u"直属标志", nullable=True)
        image_id = getp(request.POST.get("image_id", ""), u"头像图片", nullable=True)
        position = getp(request.POST.get("position", ""), u"职位信息", nullable=True)
        introduction = getp(request.POST.get("introduction", ""), u"个人介绍", nullable=True)
        area_id = getp(request.POST.get("area_id"), u"区域ID", nullable=True)
        direct_area_id = getp(request.POST.get("direct_area_id"), u"哪一个区域直属", nullable=True)

    except InvalidHttpParaException as ex:
        logger.exception(ex)
        return response_parameter_error(ex)
    try:
        result = services.mod_expert_user(request.user, expert_id, username, name, sex, institution,
                                          image_id, position, introduction, area_id, direct_area_id)
    except Exception as ex:
        logger.exception(ex)
        return response_exception(ex, ex.message)
    log_response(request, result)
    return response200(result)


@validate("POST")
def api_delete_expert_user(request):
    log_request(request)
    try:
        cur_user_id = getp(request.POST.get("cur_user_id"), u"当前用户的id")
        expert_id_list = getp(request.POST.get("expert_id_list"), u"专家的id列表", nullable=True)
        name = getp(request.POST.get("name"), u"姓名", nullable=True)
        area_id = getp(request.POST.get("area_id"), u"地域id", nullable=True)
        manage_direct = getp(request.POST.get("manage_direct"), u"直属标志", nullable=True)
        del_all_expert = getp(request.POST.get("del_all_expert"), u"是否删除所有专家", nullable=True)

    except InvalidHttpParaException as ex:
        logger.exception(ex)
        return response_parameter_error(ex)
    try:
        result = services.delete_expert_user(request.user, cur_user_id, expert_id_list, name, area_id, manage_direct, del_all_expert)
    except Exception as ex:
        logger.exception(ex)
        return response_exception(ex, ex.message)
    log_response(request, result)
    return response200(result)


@validate("POST", auth=False)
def api_detail_expert(request):
    log_request(request)
    try:
        expert_id = getp(request.POST.get("expert_id"), u"专家的id")
    except InvalidHttpParaException as ex:
        logger.exception(ex)
        return response_parameter_error(ex)
    try:
        result = services.detail_expert(request.user, expert_id)
    except Exception as ex:
        logger.exception(ex)
        return response_exception(ex, ex.message)
    log_response(request, result)
    return response200(result)


@validate("POST", auth=False)
def api_display_expert(request):
    log_request(request)
    try:
        area_id = getp(request.POST.get("area_id"), u"地域id")
    except InvalidHttpParaException as ex:
        logger.exception(ex)
        return response_parameter_error(ex)
    try:
        result = services.display_expert(request.user, area_id)
    except Exception as ex:
        logger.exception(ex)
        return response_exception(ex, ex.message)
    log_response(request, result)
    return response200(result)
