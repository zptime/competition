#!/usr/bin/python
# -*- coding=utf-8 -*-
from django.http import HttpResponse

from utils.check_auth import validate
from utils.check_param import getp
from utils.public_fun import *

import agents
import json
import traceback
import logging

from utils.utils_log import log_response

logger = logging.getLogger(__name__)


@validate('POST', auth=False)
def api_list_total_statistics(request):
    try:
        activity_id = request.POST.get('activity_id', '')
        dictResp = agents.list_total_statistics(user=request.user, activity_id=activity_id)
        log_response(request, dictResp)
        return HttpResponse(json.dumps(dictResp, ensure_ascii=False), content_type="application/json")

    except Exception as ex:
        sErrInfo = traceback.format_exc()
        logger.error(sErrInfo)
        dictResp = {"c": -1, "m": ex.message}
        return HttpResponse(json.dumps(dictResp, ensure_ascii=False), content_type="application/json")


@validate('POST', auth=False)
def api_list_country_statistics(request):
    try:
        activity_id = request.POST.get('activity_id', '')
        dictResp = agents.list_country_statistics(user=request.user, activity_id=activity_id)

        log_response(request, dictResp)
        return HttpResponse(json.dumps(dictResp, ensure_ascii=False), content_type="application/json")

    except Exception as ex:
        sErrInfo = traceback.format_exc()
        logger.error(sErrInfo)
        dictResp = {"c": -1, "m": ex.message}
        return HttpResponse(json.dumps(dictResp, ensure_ascii=False), content_type="application/json")


@validate('POST', auth=False)
def api_list_level_statistics(request):
    try:
        activity_id = getp(request.POST.get("activity_id"), u"活动ID", nullable=False)
        area_id = getp(request.POST.get("area_id"), u"区域ID", nullable=True)
        direct_level = getp(request.POST.get("direct_level"), u"直属等级（4：省直属，2市直属）", nullable=True)
        dictResp = agents.list_level_statistics(user=request.user, activity_id=activity_id, area_id=area_id, direct_level=direct_level)

        log_response(request, dictResp)
        return HttpResponse(json.dumps(dictResp, ensure_ascii=False), content_type="application/json")

    except Exception as ex:
        sErrInfo = traceback.format_exc()
        logger.error(sErrInfo)
        dictResp = {"c": -1, "m": ex.message}
        return HttpResponse(json.dumps(dictResp, ensure_ascii=False), content_type="application/json")