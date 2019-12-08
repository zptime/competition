#!/usr/bin/env python
# coding=utf-8

import logging
import traceback
from django.http import HttpResponse
import json

from applications.activity.models import Activity, ExpertActivity
from applications.score.models import FinalScore
from applications.user.models import User
from applications.work.models import Work
from utils.check_auth import validate, check
from utils.check_param import getp
from utils.const_def import FLAG_NO, FALSE_STR, TRUE_STR, FALSE_INT
from utils.const_err import ERR_WORK_ID_ERROR, ERR_USER_NOT_EXIST, SUCCESS, ERR_ACTIVITY_NOT_EXIST, ERR_EXPERT_NOT_EXIST
from utils.net_helper import response_exception, response200
from utils.utils_except import BusinessException
from utils.utils_log import log_response
import applications.score.services as score_s

logger = logging.getLogger(__name__)


@check('POST', para=(
    {'name': 'work_id'},
    {'name': 'all', 'default': FALSE_STR},
))
def api_detail_score(request, para):
    try:
        work = Work.objects.filter(id=int(para.work_id)).first()
        if not work:
            raise BusinessException(ERR_WORK_ID_ERROR)
        if para.all == FALSE_STR:
            result = score_s.get_score(request.user, work)
        else:
            result = score_s.load_all_score(request.user, work)
    except Exception as ex:
        logger.exception(ex)
        return response_exception(ex)
    return response200({'c': SUCCESS[0], 'm': SUCCESS[1], 'd': result})


@check('POST', para=(
    {'name': 'work_id'},
    {'name': 'data', 'default': ''},
    {'name': 'is_submit', 'default': FALSE_INT},
))
def api_edit_score(request, para):
    try:
        work = Work.objects.filter(id=int(para.work_id)).first()
        if not work:
            raise BusinessException(ERR_WORK_ID_ERROR)
        score_s.score(request.user, work, para.data, para.is_submit)
    except Exception as ex:
        logger.exception(ex)
        return response_exception(ex)
    return response200({'c': SUCCESS[0], 'm': SUCCESS[1]})


@check('POST', para=(
    {'name': 'activity_id'},
    {'name': 'work_id_list'},
    {'name': 'is_final', 'default': FALSE_STR},
))
def api_submit_score(request, para):
    try:
        activity = Activity.objects.get(pk=int(para.activity_id))
        if not activity:
            raise BusinessException(ERR_ACTIVITY_NOT_EXIST)
        ea = ExpertActivity.objects.filter(activity=activity, expert__del_flag=FALSE_INT, expert__account=request.user).first()
        if not ea:
            raise BusinessException(ERR_EXPERT_NOT_EXIST)
        work_id_list = [int(each) for each in para.work_id_list.strip().strip(',').split(',') if each]
        work_list = list(Work.objects.filter(id__in=work_id_list))
        result = score_s.submit_score(request.user, activity, ea.expert, work_list, para.is_final)
    except Exception as ex:
        logger.exception(ex)
        return response_exception(ex)
    return response200(result)
