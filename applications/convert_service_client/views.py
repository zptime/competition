#!/usr/bin/env python
# coding=utf-8

from django.http import HttpResponse
import traceback
import agents
import json
import logging
# from ...utils.request_auth import auth_check
from util_tools import auth_check

logger = logging.getLogger(__name__)


def api_convert_send_data(request):
    dict_resp = auth_check(request, "POST", check_login=False)
    if dict_resp != {}:
        return HttpResponse(json.dumps(dict_resp, ensure_ascii=False), content_type='application/json')
    try:
        prefix = request.POST.get("prefix")
        obj_id = request.POST.get("obj_id")
        dict_resp = agents.convert_send_data(prefix=prefix, obj_id=obj_id)
        return HttpResponse(json.dumps(dict_resp, ensure_ascii=False), content_type="application/json")
    except Exception as ex:
        str_error_info = traceback.format_exc()
        logger.error(str_error_info)
        dict_resp = dict(c=-1, m=ex.message)
        return HttpResponse(json.dumps(dict_resp, ensure_ascii=False), content_type="application/json")


def api_convert_receive_data(request):
    dict_resp = auth_check(request, "POST", check_login=False)
    if dict_resp != {}:
        return HttpResponse(json.dumps(dict_resp, ensure_ascii=False), content_type="application/json")
    try:
        src_url = request.POST.get("src_url")
        des_url = request.POST.get("des_url")
        img_url = request.POST.get("img_url")
        task_status = request.POST.get("task_status")
        task_output = request.POST.get("task_output")
        task_time = request.POST.get("task_time")
        dict_resp = agents.process_receive_data(src_url, des_url, img_url, task_status, task_output, task_time)
        return HttpResponse(json.dumps(dict_resp, ensure_ascii=False), content_type="application/json")
    except Exception as ex:
        str_err_info = traceback.format_exc()
        logger.error(str_err_info)
        dict_resp = dict(c=-1, m=ex.message)
        return HttpResponse(json.dumps(dict_resp, ensure_ascii=False), content_type="application/json")
