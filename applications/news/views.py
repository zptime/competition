#!/usr/bin/env python
# coding=utf-8
from utils.check_auth import validate
from utils.check_param import getp
from utils.net_helper import response_exception, response200
from utils.public_fun import paging_with_request
from utils.const_err import *
from utils.utils_except import BusinessException
from utils.utils_log import *
from django.http import HttpResponse
import agents
import json
import traceback
import logging

logger = logging.getLogger(__name__)


@validate("POST", False)
def api_list_news(request):
    try:
        verbose = request.POST.get("verbose")
        area_id = request.POST.get("area_id")
        dict_resp = agents.list_news(request.user, area_id, verbose)
        if dict_resp["c"] != SUCCESS[0]:
            return HttpResponse(json.dumps(dict_resp, ensure_ascii=False), content_type="application/json")
        else:
            dict_resp = paging_with_request(request, dict_resp)
            return HttpResponse(json.dumps(dict_resp, ensure_ascii=False), content_type="application/json")
    except Exception as ex:
        sErrInfo = traceback.format_exc()
        logger.error(sErrInfo)
        dict_resp = dict(c=-1, m=ex.message)
        return HttpResponse(json.dumps(dict_resp, ensure_ascii=False), content_type="application/json")


@validate("POST")
def api_add_news(request):
    try:
        title = request.POST.get("title")
        content = request.POST.get("content")
        news_type_id = request.POST.get("news_type_id")
        is_top = request.POST.get("is_top")
        status = request.POST.get("status")
        area_id = request.POST.get("area_id")
        image_id = request.POST.get("image_id", "")
        is_home_image_show = request.POST.get("is_home_image_show", '0')
        dict_resp = agents.add_news(request.user, title, content, news_type_id, is_top, status, area_id, image_id, is_home_image_show)
        return HttpResponse(json.dumps(dict_resp, ensure_ascii=False), content_type="application/json")
    except Exception as ex:
        sErrInfo = traceback.format_exc()
        logger.error(sErrInfo)
        dict_resp = dict(c=-1, m=ex.message)
        return HttpResponse(json.dumps(dict_resp, ensure_ascii=False), content_type="application/json")


@validate("POST", auth=False)
def api_detail_news(request):
    try:
        news_id = request.POST.get("news_id")
        area_id = request.POST.get("area_id")
        dict_resp = agents.detail_news(request.user, news_id, area_id)
        return HttpResponse(json.dumps(dict_resp, ensure_ascii=False), content_type="application/json")
    except Exception as ex:
        sErrInfo = traceback.format_exc()
        logger.error(sErrInfo)
        dict_resp = dict(c=-1, m=ex.message)
        return HttpResponse(json.dumps(dict_resp, ensure_ascii=False), content_type="application/json")


@validate("POST")
def api_update_news(request):
    try:
        news_id = request.POST.get("news_id")
        title = request.POST.get("title")
        content = request.POST.get("content")
        news_type_id = request.POST.get("news_type_id")
        is_top = request.POST.get("is_top")
        status = request.POST.get("status")
        image_id = request.POST.get("image_id", "")
        is_home_image_show = request.POST.get("is_home_image_show", 0)
        dict_resp = agents.update_news(request.user, news_id, title, content, news_type_id, is_top, status, image_id, is_home_image_show)
        return HttpResponse(json.dumps(dict_resp, ensure_ascii=False), content_type="application/json")
    except Exception as ex:
        sErrInfo = traceback.format_exc()
        logger.error(sErrInfo)
        dict_resp = dict(c=-1, m=ex.message)
        return HttpResponse(json.dumps(dict_resp, ensure_ascii=False), content_type="application/json")


@validate("POST")
def api_operate_news(request):
    #dict_resp = validate(request, "POST")
    #if dict_resp != {}:
        #return HttpResponse(json.dumps(dict_resp, ensure_ascii=False), content_type="application/json")
    try:
        news_id = request.POST.get('news_id')
        news_operation = request.POST.get("news_operation")
        dict_resp = agents.operate_news(request.user, news_id, news_operation)
        return HttpResponse(json.dumps(dict_resp, ensure_ascii=False), content_type="application/json")
    except Exception as ex:
        sErrInfo = traceback.format_exc()
        logger.error(sErrInfo)
        dict_resp = dict(c=-1, m=ex.message)
        return HttpResponse(json.dumps(dict_resp, ensure_ascii=False), content_type="application/json")


@validate("POST")
def api_list_newstype(request):
    try:
        verbose = request.POST.get("verbose")
        area_id = request.POST.get("area_id")
        dict_resp = agents.list_newstype(request.user, area_id)
        if dict_resp["c"] != SUCCESS[0]:
            return HttpResponse(json.dumps(dict_resp, ensure_ascii=False), content_type="application/json")
        else:
            log_response(request, dict_resp)
            return HttpResponse(json.dumps(dict_resp, ensure_ascii=False), content_type="application/json")
    except Exception as ex:
        sErrInfo = traceback.format_exc()
        logger.error(sErrInfo)
        dict_resp = dict(c=-1, m=ex.message)
        return HttpResponse(json.dumps(dict_resp, ensure_ascii=False), content_type="application/json")


@validate("POST")
def api_add_newstype(request):
    try:
        type_name = request.POST.get("type_name")
        area_id = request.POST.get("area_id")
        dict_resp = agents.add_newstype(request.user, area_id,type_name)
        return HttpResponse(json.dumps(dict_resp, ensure_ascii=False), content_type="application/json")
    except Exception as ex:
        sErrInfo = traceback.format_exc()
        logger.error(sErrInfo)
        dict_resp = dict(c=-1, m=ex.message)
        return HttpResponse(json.dumps(dict_resp, ensure_ascii=False), content_type="application/json")


@validate("POST")
def api_update_newstype(request):
    try:
        newstype_id = request.POST.get("newstype_id")
        type_name = request.POST.get("type_name")
        dict_resp = agents.update_newstype(request.user, newstype_id, type_name)
        return HttpResponse(json.dumps(dict_resp, ensure_ascii=False), content_type="application/json")
    except Exception as ex:
        sErrInfo = traceback.format_exc()
        logger.error(sErrInfo)
        dict_resp = dict(c=-1, m=ex.message)
        return HttpResponse(json.dumps(dict_resp, ensure_ascii=False), content_type="application/json")


@validate("POST")
def api_delete_newstype(request):
    try:
        newstype_id_list = request.POST.get("newstype_id_list")
        dict_resp = agents.delete_newstype(request.user, newstype_id_list)
        return HttpResponse(json.dumps(dict_resp, ensure_ascii=False), content_type="application/json")
    except Exception as ex:
        sErrInfo = traceback.format_exc()
        logger.error(sErrInfo)
        dict_resp = dict(c=-1, m=ex.message)
        return HttpResponse(json.dumps(dict_resp, ensure_ascii=False), content_type="application/json")


@validate("GET", auth=False)
def api_list_focusnews(request):
    try:
        numbers = getp(request.GET.get('numbers'), nullable=True, para_intro='返回新闻条数')
        dict_resp = agents.api_list_focusnews(numbers)
        return response200(dict_resp)
    except BusinessException as be:
        logger.exception(be)
        return response_exception(be)
    except Exception as ex:
        sErrInfo = traceback.format_exc()
        logger.error(sErrInfo)
        dict_resp = {"c": -1, "m": ex.message}
        return HttpResponse(json.dumps(dict_resp, ensure_ascii=False), content_type="application/json")
