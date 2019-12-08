# coding=utf-8
import logging
import os
import traceback
import json
from django.http import HttpResponse
from applications.activity.models import Activity, Rule
from applications.activity.share import is_activity_owner
from applications.team.models import Team
from applications.work.share import get_user
from utils.check_auth import validate, check
from utils.check_param import getp
from utils.const_err import *
from utils.net_helper import gen_file_reponse, response_exception, response200
from utils.public_fun import paging_with_request, seq2list, suuid
from utils.utils_except import BusinessException
from utils.utils_log import log_response
from applications.team import services  as t_services

logger = logging.getLogger(__name__)


@check('POST', para=(
    {'name': 'activity_id'},
    {'name': 'keyword', 'default': None},
    {'name': 'judger', 'default': None},
    {'name': 'id_list', 'default': None},  # not used yet
    {'name': 'page', 'default': '1'},
    {'name': 'rows', 'default': '10'},
))
def api_list_team_by_super(request, para):
    try:
        activity = Activity.objects.filter(id=int(para.activity_id)).first()
        if not activity:
            raise BusinessException(ERR_ACTIVITY_NOT_EXIST)
        user, role = get_user(activity, request.user)
        if not user:
            raise BusinessException(ERR_USER_AUTH)
        result = t_services.list_team_by_super(
                request.user, activity, para.keyword, para.judger, para.page, para.rows)
    except Exception as ex:
        logger.exception(ex)
        return response_exception(ex, ex.message)
    return response200({'c': SUCCESS[0], 'm': SUCCESS[1], 'd':result})


@check('POST', para=(
    {'name': 'activity_id'},
    {'name': 'team_id_list'},
))
def api_export_team_by_super(request, para):
    try:
        activity = Activity.objects.filter(id=int(para.activity_id)).first()
        if not activity:
            raise BusinessException(ERR_ACTIVITY_NOT_EXIST)
        user, role = get_user(activity, request.user)
        if not user:
            raise BusinessException(ERR_USER_AUTH)
        if not is_activity_owner(activity, request.user):
            raise BusinessException(ERR_USER_AUTH)
        team_id_list = [int(each) for each in para.team_id_list.strip().strip(',').split(',') if each]
        # team_list = list(Team.objects.filter(id__in=team_id_list))
        wb = t_services.export_team_by_super(request.user, activity, user, role, team_id_list)

        fname = u'%s.xlsx' % suuid()
        response = HttpResponse(content_type='application/vnd.ms-excel')
        response['Content-Disposition'] = 'attachment; filename=' + fname.encode('utf-8')
        wb.save(response)
        return response

        # path = os.path.join(settings.BASE_DIR, 'media/%s.xlsx' % suuid())
        # wb.save(path)
        # return response200({'c': SUCCESS[0], 'm': SUCCESS[1], 'd': path})
    except Exception as ex:
        logger.exception(ex)
        return response_exception(ex, ex.message)


@check('POST', para=(
    {'name': 'activity_id'},
    {'name': 'only_leader_team', 'default': None},
    {'name': 'id_list', 'default': None},    # not used yet
    {'name': 'page', 'default': '1'},
    {'name': 'rows', 'default': '10'},
))
def api_list_team_by_judger(request, para):
    try:
        activity = Activity.objects.filter(id=int(para.activity_id)).first()
        if not activity:
            raise BusinessException(ERR_ACTIVITY_NOT_EXIST)
        # user, role = get_user(activity, request.user)
        # if not user:
        #     raise BusinessException(ERR_USER_AUTH)
        result = t_services.list_team_by_judger(
                request.user, activity, para.only_leader_team, para.page, para.rows)
    except Exception as ex:
        logger.exception(ex)
        return response_exception(ex, ex.message)
    return response200({'c': SUCCESS[0], 'm': SUCCESS[1], 'd':result})


@check('POST', para=(
    {'name': 'activity_id'},
    {'name': 'team_id', 'default': None},
    {'name': 'new_name', 'default': None},
))
def api_edit_team(request, para):
    try:
        activity = Activity.objects.filter(id=int(para.activity_id)).first()
        if not activity:
            raise BusinessException(ERR_ACTIVITY_NOT_EXIST)
        team = Team.objects.filter(id=int(para.team_id)).first() if para.team_id else None
        result = t_services.edit_team(request.user, activity, team, para.new_name)
    except Exception as ex:
        logger.exception(ex)
        return response_exception(ex, ex.message)
    return response200({'c': SUCCESS[0], 'm': SUCCESS[1], 'd':result})


@check('POST', para=(
    {'name': 'activity_id'},
    {'name': 'team_id_list', 'default': None},
))
def api_delete_team(request, para):
    try:
        activity = Activity.objects.filter(id=int(para.activity_id)).first()
        if not activity:
            raise BusinessException(ERR_ACTIVITY_NOT_EXIST)
        team_id_list = [int(each) for each in para.team_id_list.strip().strip(',').split(',')]
        team_list = Team.objects.filter(id__in=team_id_list)
        result = t_services.delete_team(request.user, activity, team_list)
    except Exception as ex:
        logger.exception(ex)
        return response_exception(ex, ex.message)
    return response200({'c': SUCCESS[0], 'm': SUCCESS[1], 'd':result})


@check('POST', para=(
    {'name': 'activity_id'},
    {'name': 'team_id'},
    {'name': 'work_id_list', 'default': None},
))
def api_add_team_work(request, para):
    try:
        activity = Activity.objects.filter(id=int(para.activity_id)).first()
        if not activity:
            raise BusinessException(ERR_ACTIVITY_NOT_EXIST)
        team = Team.objects.filter(id=int(para.team_id)).first()
        if not team:
            raise BusinessException(ERR_TEAM_NOT_EXIST)
        work_id_list = [int(each) for each in para.work_id_list.strip().strip(',').split(',') if each]
        # work_list = list(Work.objects.filter(id__in=work_id_list))
        result = t_services.add_team_work(request.user, activity, team, work_id_list)
    except Exception as ex:
        logger.exception(ex)
        return response_exception(ex, ex.message)
    return response200({'c': SUCCESS[0], 'm': SUCCESS[1], 'd':result})


@check('POST', para=(
    {'name': 'activity_id'},
    {'name': 'team_id'},
    {'name': 'work_id_list', 'default': None},
))
def api_remove_team_work(request, para):
    try:
        activity = Activity.objects.filter(id=int(para.activity_id)).first()
        if not activity:
            raise BusinessException(ERR_ACTIVITY_NOT_EXIST)
        team = Team.objects.filter(id=int(para.team_id)).first()
        if not team:
            raise BusinessException(ERR_TEAM_NOT_EXIST)
        work_id_list = [int(each) for each in para.work_id_list.strip().strip(',').split(',') if each]
        # work_list = list(Work.objects.filter(id__in=work_id_list))
        result = t_services.remove_team_work(request.user, activity, team, work_id_list)
    except Exception as ex:
        logger.exception(ex)
        return response_exception(ex, ex.message)
    return response200({'c': SUCCESS[0], 'm': SUCCESS[1], 'd':result})


@check('POST', para=(
    {'name': 'team_id'},
))
def api_detail_team(request, para):
    # 获取组信息和组内专家信息
    try:
        team = Team.objects.filter(id=int(para.team_id)).first()
        if not team:
            raise BusinessException(ERR_TEAM_NOT_EXIST)
        rule = Rule.objects.filter(activity=team.activity).first()
        if not rule:
            raise BusinessException(ERR_RULE_NOT_EXIST)
        max = str(rule.parse_rule().expert_count())
        result = t_services.detail_team(team, max)
    except Exception as ex:
        logger.exception(ex)
        return response_exception(ex, ex.message)
    return response200({'c': SUCCESS[0], 'm': SUCCESS[1], 'd':result})


@check('POST', para=(
    {'name': 'team_id'},
    {'name': 'keyword', 'default': None},
    {'name': 'expert_in_same_team', 'default': list()},
    {'name': 'page', 'default': '1'},
    {'name': 'rows', 'default': '10'},
))
def api_available_add_expert_in_team(request, para):
    try:
        team = Team.objects.filter(id=int(para.team_id)).first()
        if not team:
            raise BusinessException(ERR_TEAM_NOT_EXIST)
        in_team_page = list()
        if para.expert_in_same_team:
            in_team_page = [int(each) for each in seq2list(para.expert_in_same_team)]
        result = t_services.available_add_expert_in_team(request.user, team, in_team_page, para.keyword, para.page, para.rows)
    except Exception as ex:
        logger.exception(ex)
        return response_exception(ex, ex.message)
    return response200({'c': SUCCESS[0], 'm': SUCCESS[1], 'd':result})


@check('POST', para=(
    {'name': 'team_id'},
))
def api_list_expert_area_in_team(request, para):
    try:
        team = Team.objects.filter(id=int(para.team_id)).first()
        if not team:
            raise BusinessException(ERR_TEAM_NOT_EXIST)
        result = t_services.list_expert_area_in_team(request.user, team)
    except Exception as ex:
        logger.exception(ex)
        return response_exception(ex, ex.message)
    return response200({'c': SUCCESS[0], 'm': SUCCESS[1], 'd':result})


@check('POST', para=(
    {'name': 'team_id'},
    {'name': 'new_expert_json'},
))
def api_update_expert_in_team(request, para):
    try:
        team = Team.objects.filter(id=int(para.team_id)).first()
        if not team:
            raise BusinessException(ERR_TEAM_NOT_EXIST)
        user, role = get_user(team.activity, request.user)
        if not user:
            raise BusinessException(ERR_USER_AUTH)
        result = t_services.update_expert_in_team(request.user, user, role, team, para.new_expert_json)
    except Exception as ex:
        logger.exception(ex)
        return response_exception(ex, ex.message)
    return response200({'c': SUCCESS[0], 'm': SUCCESS[1], 'd':result})



