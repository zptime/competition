# -*- coding=utf-8 -*-
import json
import logging
import traceback

from django.conf import settings
from django.http import HttpResponse

from applications.activity.models import Activity, Ranks, ExpertActivity, Role
from applications.activity.share import is_activity_owner
from applications.expert.models import Expert
from applications.team.models import Team
from applications.upload_resumable.models import FileObj
from applications.user.models import Area, User
from applications.work import agents
from applications.work.export import WorkExcelExport, EXCEL
from applications.work.models import Work
from applications.work.share import get_user
from utils.check_auth import validate, check
from utils.check_param import getp
from utils.const_def import FALSE_INT, FLAG_NO
from utils.const_err import *
from utils.net_helper import response_exception, response200, response_parameter_error, gen_file_reponse, get_cur_domain
from utils.public_fun import paging_with_request, get_pre_and_next

from utils.utils_except import BusinessException
from utils.utils_log import log_request, log_response

logger = logging.getLogger(__name__)

# TODO cur_user_id shoube be self account


@check('POST', para=(
    {'name': 'activity_id'},
    {'name': 'work_info'},
))
def api_create_work(request, para):
    try:
        activity = Activity.objects.filter(id=int(para.activity_id)).first()
        if not activity:
            raise BusinessException(ERR_ACTIVITY_NOT_EXIST)
        user, role = get_user(activity, request.user)
        if not user:
            raise BusinessException(ERR_USER_AUTH)
        dict_resp = agents.create_work(user, role, activity, para.work_info)
        return HttpResponse(json.dumps(dict_resp, ensure_ascii=False), content_type="application/json")
    except Exception as e:
        logger.exception(e)
        return response_exception(e)


# @check('POST')
# def api_commit_work(request):
#     try:
#         is_publish = request.POST.get("is_publish", "")
#         work_id_list = request.POST.get("work_id_list", "")
#         dict_resp = agents.commit_work(request.user, is_publish, work_id_list)
#         return HttpResponse(json.dumps(dict_resp, ensure_ascii=False), content_type="application/json")
#     except BusinessException as be:
#         logger.exception(be)
#         return response_exception(be)
#     except Exception as ex:
#         logger.exception(ex)
#         return HttpResponse(json.dumps(dict_resp, ensure_ascii=False), content_type="application/json")


"""
  list_work:
    超管查看作品  
    地区管理员查看/审批作品  
    上传者查看作品  
    专家查看作品  
    专家组长查看作品  
    分组中的作品  
    待添加到分组中的作品  
    专家查看作品 （子级评审）  
    专家组长查看作品 （子级评审）  
    分组中的作品 （子级评审） 
    待添加到分组中的作品 （子级评审）
"""

@check('POST', para=(
    {'name': 'activity_id'},
    {'name': 'is_all', 'default': '0'},
    {'name': 'sub_activity', 'default': None},   # 过滤条件
    {'name': 'phase', 'default': None},   # 过滤条件
    {'name': 'project', 'default': None},   # 过滤条件
    {'name': 'subject', 'default': None},  # 过滤条件
    {'name': 'area_id', 'default': None},   # 过滤条件
    {'name': 'direct_area_id', 'default': None},   # 过滤条件
    {'name': 'rank_id', 'default': None},   # 过滤条件
    {'name': 'team_id', 'default': None},   # 过滤条件
    {'name': 'keyword', 'default': None},   # 过滤条件
    {'name': 'status', 'default': None},   # 过滤条件
    {'name': 'is_public', 'default': None},   # 过滤条件
    {'name': 'page', 'default': '1'},
    {'name': 'rows', 'default': '10'},
))
def api_list_work_super(request, para):
    try:
        activity = Activity.objects.filter(id=int(para.activity_id)).first()
        if not activity:
            raise BusinessException(ERR_ACTIVITY_NOT_EXIST)
        area = Area.objects.filter(id=int(para.area_id)).first() if para.area_id else None
        direct_area = Area.objects.filter(id=int(para.direct_area_id)).first() if para.direct_area_id else None
        rank = Ranks.objects.filter(id=int(para.rank_id)).first() if para.rank_id else None
        team = Team.objects.filter(id=int(para.team_id)).first() if para.team_id else None
        user, role = get_user(activity, request.user)
        if not user:
            raise BusinessException(ERR_USER_AUTH)
        # 只有活动的创建者可以访问
        if not is_activity_owner(activity, request.user):
            raise BusinessException(ERR_USER_AUTH)
        status_list = para.status.strip().strip(',').split(',') if para.status else None
        result = agents.list_work_super(
                request.user, user, activity, int(para.is_all), para.sub_activity, para.phase,
                para.project, area, direct_area, para.subject, rank, team, para.keyword, status_list,
                para.is_public, para.page, para.rows,
        )
    except Exception as ex:
        logger.exception(ex)
        return response_exception(ex, ex.message)
    return response200({'c': SUCCESS[0], 'm': SUCCESS[1], 'd':result})


@check('POST', para=(
    {'name': 'activity_id'},
    {'name': 'work_id_list'},
))
def api_export_work_super(request, para):
    try:
        activity = Activity.objects.filter(id=int(para.activity_id)).first()
        if not activity:
            raise BusinessException(ERR_ACTIVITY_NOT_EXIST)
        work_id_list = [int(each) for each in para.work_id_list.strip().strip(',').split(',') if each]
        work_list = list(Work.objects.filter(id__in=work_id_list))

        if not is_activity_owner(activity, request.user):
            raise BusinessException(ERR_USER_AUTH)

        resp = WorkExcelExport(activity, work_list,
                (EXCEL.BASIC, EXCEL.STATUS, EXCEL.AUTHOR, EXCEL.TUTOR, EXCEL.FINAL_SCORE, EXCEL.SCORE))\
                .write().dump_stream()
        return resp
    except Exception as ex:
        logger.exception(ex)
        return response_exception(ex, ex.message)


@check('POST', para=(
    {'name': 'activity_id'},
    {'name': 'work_id_list'},
))
def api_export_work_super_all(request, para):
    try:
        activity = Activity.objects.filter(id=int(para.activity_id)).first()
        if not activity:
            raise BusinessException(ERR_ACTIVITY_NOT_EXIST)
        # work_id_list = [int(each) for each in para.work_id_list.strip().strip(',').split(',') if each]
        # work_list = list(Work.objects.filter(id__in=work_id_list))

        if not is_activity_owner(activity, request.user):
            raise BusinessException(ERR_USER_AUTH)

        result = agents.export_work_super_all(request.user, activity, para.work_id_list)
        return response200({'c': SUCCESS[0], 'm': SUCCESS[1], 'd': result})
    except Exception as ex:
        logger.exception(ex)
        return response_exception(ex)


@check("POST", para=(
        {'name': 'activity_id'},
))
def api_export_work_super_download(request, para):
    try:
        activity = Activity.objects.filter(id=int(para.activity_id)).first()
        if not activity:
            raise BusinessException(ERR_ACTIVITY_NOT_EXIST)
        path = agents.export_work_super_download(request.user, activity)
        return gen_file_reponse(path)
    except Exception as ex:
        logger.exception(ex)
        return response_exception(ex)


@check('POST', para=(
    {'name': 'activity_id'},
    {'name': 'sub_activity', 'default': None},   # 过滤条件
    {'name': 'phase', 'default': None},   # 过滤条件
    {'name': 'project', 'default': None},   # 过滤条件
    {'name': 'area_id', 'default': None},   # 过滤条件
    {'name': 'direct_area_id', 'default': None},   # 过滤条件
    {'name': 'subject', 'default': None},   # 过滤条件
    {'name': 'keyword', 'default': None},   # 过滤条件
    {'name': 'is_approve', 'default': None},   # 过滤条件
    {'name': 'page', 'default': '1'},
    {'name': 'rows', 'default': '10'},
))
def api_list_work_manager(request, para):
    activity = Activity.objects.filter(id=int(para.activity_id)).first()
    if not activity:
        raise BusinessException(ERR_ACTIVITY_NOT_EXIST)
    user, role = get_user(activity, request.user)
    if not user:
        raise BusinessException(ERR_USER_AUTH)
    area = Area.objects.filter(id=int(para.area_id)).first() if para.area_id else None
    direct_area = Area.objects.filter(id=int(para.direct_area_id)).first() if para.direct_area_id else None
    try:
        result = agents.list_work_manager(
                request.user, user, activity, para.is_approve, para.sub_activity, para.phase,
                para.project, area, direct_area, para.subject, para.keyword,
                para.page, para.rows,
        )
    except Exception as ex:
        logger.exception(ex)
        return response_exception(ex, ex.message)
    return response200({'c': SUCCESS[0], 'm': SUCCESS[1], 'd':result})


@check('POST', para=(
    {'name': 'activity_id'},
    {'name': 'work_id_list'},
))
def api_export_work_manager(request, para):
    try:
        activity = Activity.objects.filter(id=int(para.activity_id)).first()
        if not activity:
            raise BusinessException(ERR_ACTIVITY_NOT_EXIST)
        work_id_list = [int(each) for each in para.work_id_list.strip().strip(',').split(',') if each]
        work_list = list(Work.objects.filter(id__in=work_id_list))

        # TODO check auth for these work
        #

        resp = WorkExcelExport(activity, work_list,
                (EXCEL.BASIC, EXCEL.AUTHOR, EXCEL.TUTOR))\
                .write().dump_stream()
        return resp
    except Exception as ex:
        logger.exception(ex)
        return response_exception(ex, ex.message)


@check('POST', para=(
    {'name': 'activity_id'},
    {'name': 'sub_activity', 'default': None},   # 过滤条件
    {'name': 'phase', 'default': None},   # 过滤条件
    {'name': 'project', 'default': None},   # 过滤条件
    {'name': 'area_id', 'default': None},   # 过滤条件
    {'name': 'direct_area_id', 'default': None},   # 过滤条件
    {'name': 'subject', 'default': None},   # 过滤条件
    {'name': 'keyword', 'default': None},   # 过滤条件
    {'name': 'team_id'},   # 过滤条件
    {'name': 'page', 'default': '1'},
    {'name': 'rows', 'default': '10'},
))
def api_list_work_in_team(request, para):
    try:
        activity = Activity.objects.filter(id=int(para.activity_id)).first()
        if not activity:
            raise BusinessException(ERR_ACTIVITY_NOT_EXIST)
        area = Area.objects.filter(id=int(para.area_id)).first() if para.area_id else None
        direct_area = Area.objects.filter(id=int(para.direct_area_id)).first() if para.direct_area_id else None
        team = Team.objects.filter(id=int(para.team_id)).first()
        if not team:
            raise BusinessException(ERR_TEAM_EMPTY)
        user, role = get_user(activity, request.user)
        if not user:
            raise BusinessException(ERR_USER_AUTH)
        # 只有活动的创建者可以访问
        if not is_activity_owner(activity, request.user):
            raise BusinessException(ERR_USER_AUTH)
        result = agents.list_work_in_team(
                request.user, user, activity, para.sub_activity, para.phase,
                para.project, area, direct_area, para.subject, para.keyword, team,
                para.page, para.rows,
        )
    except Exception as ex:
        logger.exception(ex)
        return response_exception(ex, ex.message)
    return response200({'c': SUCCESS[0], 'm': SUCCESS[1], 'd':result})


@check('POST', para=(
    {'name': 'activity_id'},
    {'name': 'team_id'},
    {'name': 'sub_activity', 'default': None},   # 过滤条件
    {'name': 'phase', 'default': None},   # 过滤条件
    {'name': 'project', 'default': None},   # 过滤条件
    {'name': 'area_id', 'default': None},   # 过滤条件
    {'name': 'direct_area_id', 'default': None},   # 过滤条件
    {'name': 'subject', 'default': None},   # 过滤条件
    {'name': 'keyword', 'default': None},   # 过滤条件
    {'name': 'ignore_area_id',  'default': None},   # 过滤条件
    {'name': 'page', 'default': '1'},
    {'name': 'rows', 'default': '10'},
))
def api_list_work_avalable_add_team(request, para):
    try:
        activity = Activity.objects.filter(id=int(para.activity_id)).first()
        if not activity:
            raise BusinessException(ERR_ACTIVITY_NOT_EXIST)
        area = Area.objects.filter(id=int(para.area_id)).first() if para.area_id else None
        direct_area = Area.objects.filter(id=int(para.direct_area_id)).first() if para.direct_area_id else None
        ignore_area_list = para.ignore_area_id.strip().strip(',').split(',') if para.ignore_area_id else []
        team = Team.objects.filter(id=int(para.team_id)).first()
        if not team:
            raise BusinessException(ERR_TEAM_EMPTY)
        user, role = get_user(activity, request.user)
        if not user:
            raise BusinessException(ERR_USER_AUTH)
        # 只有活动的创建者可以访问
        if not is_activity_owner(activity, request.user):
            raise BusinessException(ERR_USER_AUTH)
        result = agents.list_work_avalable_add_team(
                request.user, user, team, activity, para.sub_activity, para.phase,
                para.project, area, direct_area, para.subject, para.keyword, ignore_area_list,
                para.page, para.rows,
        )
    except Exception as ex:
        logger.exception(ex)
        return response_exception(ex, ex.message)
    return response200({'c': SUCCESS[0], 'm': SUCCESS[1], 'd':result})


@check('POST', para=(
    {'name': 'activity_id'},
    {'name': 'sub_activity', 'default': None},   # 过滤条件
    {'name': 'phase', 'default': None},   # 过滤条件
    {'name': 'project', 'default': None},   # 过滤条件
    {'name': 'subject', 'default': None},   # 过滤条件
    {'name': 'keyword', 'default': None},   # 过滤条件
    {'name': 'team', 'default': None},   # 过滤条件
    {'name': 'is_unfinish', 'default': FALSE_INT},   # 过滤条件
    {'name': 'page', 'default': '1'},
    {'name': 'rows', 'default': '10'},
))
def api_list_work_expert(request, para):
    try:
        activity = Activity.objects.filter(id=int(para.activity_id)).first()
        if not activity:
            raise BusinessException(ERR_ACTIVITY_NOT_EXIST)
        team = Team.objects.filter(id=int(para.team)).first() if para.team else None
        ea = ExpertActivity.objects.filter(activity=activity, expert__del_flag=FALSE_INT, expert__account=request.user).first()
        if not ea:
            raise BusinessException(ERR_USER_AUTH)
        result = agents.list_work_expert(
            request.user, ea.expert, activity, para.sub_activity, para.phase, para.project, para.subject, para.keyword,
            team, para.is_unfinish, para.page, para.rows,
        )
        return response200({'c': SUCCESS[0], 'm': SUCCESS[1], 'd': result})
    except Exception as ex:
        logger.exception(ex)
        return response_exception(ex, ex.message)


@check('POST', para=(
    {'name': 'activity_id'},
    {'name': 'work_id_list'},
))
def api_export_work_expert(request, para):
    try:
        activity = Activity.objects.filter(id=int(para.activity_id)).first()
        if not activity:
            raise BusinessException(ERR_ACTIVITY_NOT_EXIST)
        ea = ExpertActivity.objects.filter(activity=activity, expert__del_flag=FALSE_INT, expert__account=request.user).first()
        work_id_list = [int(each) for each in para.work_id_list.strip().strip(',').split(',') if each]
        work_list = list(Work.objects.filter(id__in=work_id_list))

        # TODO check auth for these work
        #

        resp = WorkExcelExport(activity, work_list,
                (EXCEL.BASIC, EXCEL.AUTHOR, EXCEL.TUTOR, EXCEL.MY_SCORE), expert=ea.expert)\
                .write().dump_stream()
        return resp
    except Exception as ex:
        logger.exception(ex)
        return response_exception(ex, ex.message)


@check('POST', para=(
    {'name': 'activity_id'},
    {'name': 'sub_activity', 'default': None},   # 过滤条件
    {'name': 'phase', 'default': None},   # 过滤条件
    {'name': 'project', 'default': None},   # 过滤条件
    {'name': 'subject', 'default': None},   # 过滤条件
    {'name': 'keyword', 'default': None},   # 过滤条件
    {'name': 'team', 'default': None},   # 过滤条件
    {'name': 'is_unfinish', 'default': None},   # 过滤条件
    {'name': 'page', 'default': '1'},
    {'name': 'rows', 'default': '10'},
))
def api_list_work_leader(request, para):
    activity = Activity.objects.filter(id=int(para.activity_id)).first()
    if not activity:
        raise BusinessException(ERR_ACTIVITY_NOT_EXIST)
    team = Team.objects.filter(id=int(para.team)).first() if para.team else None
    ea = ExpertActivity.objects.filter(
            activity=activity, expert__del_flag=FALSE_INT, expert__account=request.user).first()

    is_unfinish = int(para.is_unfinish) if para.is_unfinish else None
    try:
        result= agents.list_work_leader(
            request.user, ea.expert, activity, para.sub_activity, para.phase, para.project, para.subject, para.keyword,
            team, is_unfinish, para.page, para.rows,
        )
    except Exception as ex:
        logger.exception(ex)
        return response_exception(ex)
    return response200({'c': SUCCESS[0], 'm': SUCCESS[1], 'd':result})


@check('POST', para=(
    {'name': 'activity_id'},
    {'name': 'work_id_list'},
))
def api_export_work_leader(request, para):
    try:
        activity = Activity.objects.filter(id=int(para.activity_id)).first()
        if not activity:
            raise BusinessException(ERR_ACTIVITY_NOT_EXIST)
        ea = ExpertActivity.objects.filter(activity=activity, expert__del_flag=FALSE_INT, expert__account=request.user).first()
        # TODO 验证必须是组长
        #

        work_id_list = [int(each) for each in para.work_id_list.strip().strip(',').split(',') if each]
        work_list = list(Work.objects.filter(id__in=work_id_list))

        # TODO check auth for these work
        #

        resp = WorkExcelExport(activity, work_list,
                (EXCEL.BASIC, EXCEL.AUTHOR, EXCEL.TUTOR, EXCEL.MY_SCORE, EXCEL.SCORE), expert=ea.expert)\
                .write().dump_stream()
        return resp
    except Exception as ex:
        logger.exception(ex)
        return response_exception(ex, ex.message)


@check('POST', para=(
    {'name': 'activity_id'},
    {'name': 'sub_activity', 'default': None},   # 过滤条件
    {'name': 'phase', 'default': None},   # 过滤条件
    {'name': 'project', 'default': None},   # 过滤条件
    {'name': 'subject', 'default': None},   # 过滤条件
    {'name': 'keyword', 'default': None},   # 过滤条件
    {'name': 'status', 'default': None},   # 过滤条件
    {'name': 'page', 'default': '1'},
    {'name': 'rows', 'default': '10'},
))
def api_list_work_upload(request, para):
    activity = Activity.objects.filter(id=int(para.activity_id)).first()
    if not activity:
        raise BusinessException(ERR_ACTIVITY_NOT_EXIST)
    user, role = get_user(activity, request.user)
    if not user:
        raise BusinessException(ERR_USER_AUTH)
    status_list = para.status.strip().strip(',').split(',') if para.status else None
    try:
        result = agents.list_work_upload(
                request.user, user, activity, para.sub_activity, para.phase, para.project, para.subject, para.keyword,
                status_list, para.page, para.rows,
        )
    except Exception as ex:
        logger.exception(ex)
        return response_exception(ex, ex.message)
    return response200({'c': SUCCESS[0], 'm': SUCCESS[1], 'd':result})


@check('POST', para=(
    {'name': 'activity_id'},
    {'name': 'work_id_list'},
))
def api_export_work_upload(request, para):
    try:
        activity = Activity.objects.filter(id=int(para.activity_id)).first()
        if not activity:
            raise BusinessException(ERR_ACTIVITY_NOT_EXIST)
        work_id_list = [int(each) for each in para.work_id_list.strip().strip(',').split(',') if each]
        work_list = list(Work.objects.filter(id__in=work_id_list))

        # TODO check auth for these work
        #

        resp = WorkExcelExport(activity, work_list,
                (EXCEL.BASIC, EXCEL.STATUS, EXCEL.AUTHOR, EXCEL.TUTOR))\
                .write().dump_stream()
        return resp
    except Exception as ex:
        logger.exception(ex)
        return response_exception(ex, ex.message)


@validate('POST', auth=False)
def api_detail_work(request):
    try:
        work_id = request.POST.get("work_id", "")
        dict_resp = agents.detail_work(work_id, account=None)
        return HttpResponse(json.dumps(dict_resp, ensure_ascii=False), content_type="application/json")
    except Exception as e:
        logger.exception(e)
        return response_exception(e)


@check('POST', para=(
    {'name': 'work_id'},
    {'name': 'work_info'},
))
def api_update_work(request, para):
    try:
        work = Work.objects.filter(id=int(para.work_id)).first()
        if not work:
            raise BusinessException(ERR_WORK_ID_ERROR)
        user, role = get_user(work.activity, request.user)
        if not user:
            raise BusinessException(ERR_USER_AUTH)
        dict_resp = agents.update_work(request.user, user, role, work, para.work_info)
        return HttpResponse(json.dumps(dict_resp, ensure_ascii=False), content_type="application/json")
    except Exception as e:
        logger.exception(e)
        return response_exception(e)


@check('POST', para=(
    {'name': 'activity_id'},
    {'name': 'work_id_list'},
))
def api_submit_work(request, para):
    activity = Activity.objects.filter(id=int(para.activity_id)).first()
    if not activity:
        raise BusinessException(ERR_ACTIVITY_NOT_EXIST)
    user, role = get_user(activity, request.user)
    if not user:
        raise BusinessException(ERR_USER_AUTH)
    work_id_list = [int(each) for each in para.work_id_list.strip().strip(',').split(',') if each]
    work_list = list(Work.objects.filter(id__in=work_id_list))
    try:
        result = agents.submit_work(activity, user, role, work_list)
    except Exception as ex:
        logger.exception(ex)
        return response_exception(ex, ex.message)
    return response200({'c': SUCCESS[0], 'm': SUCCESS[1], 'd':result})


@check('POST', para=(
    {'name': 'activity_id'},
    {'name': 'work_id_list'},
))
def api_delete_work(request, para):
    activity = Activity.objects.filter(id=int(para.activity_id)).first()
    if not activity:
        raise BusinessException(ERR_ACTIVITY_NOT_EXIST)
    user, role = get_user(activity, request.user)
    if not user:
        raise BusinessException(ERR_USER_AUTH)
    work_id_list = [int(each) for each in para.work_id_list.strip().strip(',').split(',') if each]
    work_list = list(Work.objects.filter(id__in=work_id_list))
    try:
        result = agents.delete_work(activity, request.user, user, work_list)
    except Exception as ex:
        logger.exception(ex)
        return response_exception(ex, ex.message)
    return response200({'c': SUCCESS[0], 'm': SUCCESS[1], 'd':result})


@check('POST', para=(
    {'name': 'activity_id'},
    {'name': 'work_id_list'},
))
def api_approve_work(request, para):
    activity = Activity.objects.filter(id=int(para.activity_id)).first()
    if not activity:
        raise BusinessException(ERR_ACTIVITY_NOT_EXIST)
    user, role = get_user(activity, request.user)
    if not user:
        raise BusinessException(ERR_USER_AUTH)
    work_id_list = [int(each) for each in para.work_id_list.strip().strip(',').split(',') if each]
    work_list = list(Work.objects.filter(id__in=work_id_list))
    try:
        result = agents.approve_work(activity, user, work_list)
    except Exception as ex:
        logger.exception(ex)
        return response_exception(ex, ex.message)
    return response200({'c': SUCCESS[0], 'm': SUCCESS[1], 'd':result})


@check('POST', para=(
    {'name': 'activity_id'},
    {'name': 'work_id_list'},
))
def api_reject_work(request, para):
    activity = Activity.objects.filter(id=int(para.activity_id)).first()
    if not activity:
        raise BusinessException(ERR_ACTIVITY_NOT_EXIST)
    user, role = get_user(activity, request.user)
    if not user:
        raise BusinessException(ERR_USER_AUTH)
    work_id_list = [int(each) for each in para.work_id_list.strip().strip(',').split(',') if each]
    work_list = list(Work.objects.filter(id__in=work_id_list))
    try:
        result = agents.reject_work(activity, user, work_list)
    except Exception as ex:
        logger.exception(ex)
        return response_exception(ex, ex.message)
    return response200({'c': SUCCESS[0], 'm': SUCCESS[1], 'd':result})


@check('POST', para=(
    {'name': 'activity_id'},
    {'name': 'work_id_list'},
    {'name': 'rank_id'},
))
def api_rank_work(request, para):
    activity = Activity.objects.filter(id=int(para.activity_id)).first()
    if not activity:
        raise BusinessException(ERR_ACTIVITY_NOT_EXIST)
    user, role = get_user(activity, request.user)
    if not user:
        raise BusinessException(ERR_USER_AUTH)
    # 只有超管有本接口权限
    if not is_activity_owner(activity, request.user):
        raise BusinessException(ERR_USER_AUTH)
    work_id_list = [int(each) for each in para.work_id_list.strip().strip(',').split(',') if each]
    work_list = list(Work.objects.filter(id__in=work_id_list))
    rank = Ranks.objects.filter(id=int(para.rank_id), activity=activity).first()
    if not rank:
        raise BusinessException(ERR_RANK_ID)
    try:
        result = agents.rank_work(activity, user, work_list, rank)
    except Exception as ex:
        logger.exception(ex)
        return response_exception(ex, ex.message)
    return response200({'c': SUCCESS[0], 'm': SUCCESS[1], 'd':result})


@check('POST', auth=True, para=(
    {'name': 'work_id'},
))
def api_star_work(request, para):
    try:
        dict_resp = agents.star_work(request.user, para.work_id)
        return HttpResponse(json.dumps(dict_resp, ensure_ascii=False), content_type="application/json")
    except BusinessException as e:
        logger.exception(e)
        return response_exception(e)


@check('POST', auth=True, para=(
    {'name': 'work_id'},
    {'name': 'status', 'default': 1},  # 1：投一票，0：取消投票
))
def api_vote_work(request, para):
    try:
        dict_resp = agents.vote_work(request.user, para.work_id, para.status)
        return HttpResponse(json.dumps(dict_resp, ensure_ascii=False), content_type="application/json")
    except BusinessException as e:
        logger.exception(e)
        return response_exception(e)


@check('POST', para=(
    {'name': 'activity_id'},
    {'name': 'work_id_list'},
))
def api_download_work(request, para):
    try:
        activity = Activity.objects.filter(id=int(para.activity_id)).first()
        if not activity:
            raise BusinessException(ERR_ACTIVITY_NOT_EXIST)
        user, role = get_user(activity, request.user)
        ea = ExpertActivity.objects.filter(expert__account=request.user, activity=activity).first()
        work_id_list = [int(each) for each in para.work_id_list.strip().strip(',').split(',') if each]
        work_list = list(Work.objects.filter(id__in=work_id_list))
        result = agents.download_work(activity, request.user, role, ea, work_list)
        return response200({'c': SUCCESS[0], 'm': SUCCESS[1], 'd':result})
    except Exception as ex:
        logger.exception(ex)
        return response_exception(ex, ex.message)


@check('POST', para=(
    {'name': 'activity_id'},
    {'name': 'data'},
))
def api_match_work(request, para):
    try:
        activity = Activity.objects.filter(id=int(para.activity_id)).first()
        if not activity:
            raise BusinessException(ERR_ACTIVITY_NOT_EXIST)
        user, role = get_user(activity, request.user)
        result = agents.match_work(activity, request.user, role, para.data)
        return response200({'c': SUCCESS[0], 'm': SUCCESS[1], 'd': result})
    except Exception as ex:
        logger.exception(ex)
        return response_exception(ex, ex.message)


@validate('GET', auth=False)
def api_download_work_template(request):
    try:
        activity_id = request.GET.get("activity_id", "")
        sub_activity = request.GET.get("sub_activity", "")
        file_path = agents.download_work_template(activity_id, sub_activity)
        resp = gen_file_reponse(file_path)
        return resp
    except Exception as e:
        logger.exception(e)
        return response_exception(e)


@check('POST', para=(
    {'name': 'activity_id'},
    {'name': 'sub_activity'},
    {'name': 'file', 'is_file': True, },
))
def api_import_work(request, para):
    try:
        activity = Activity.objects.filter(id=int(para.activity_id)).first()
        if not activity:
            raise BusinessException(ERR_ACTIVITY_NOT_EXIST)
        user, role = get_user(activity, request.user)
        dict_resp = agents.import_work(request.user, user, role, activity, para.sub_activity, para.file)
        return HttpResponse(json.dumps(dict_resp, ensure_ascii=False), content_type="application/json")
    except BusinessException as e:
        logger.exception(e)
        return response_exception(e)


@validate('POST', auth=True)
def api_list_no_file_work(request):
    try:
        activity_id = request.POST.get("activity_id", "")
        activity = Activity.objects.filter(id=int(activity_id)).first()
        if not activity:
            raise BusinessException(ERR_ACTIVITY_NOT_EXIST)
        # cur_user_id = getp(request.POST.get('cur_user_id'), nullable=False, para_intro='当前用户ID')
        user, role = get_user(activity, request.user)
        if not user:
            raise BusinessException(ERR_USER_AUTH)
        dict_resp = agents.list_no_file_work(request.user, activity_id=activity_id, cur_user_id=user.id)
        dict_resp = paging_with_request(request, dict_resp)
        log_response(request, dict_resp)
        return HttpResponse(json.dumps(dict_resp, ensure_ascii=False), content_type="application/json")

    except BusinessException as be:
        logger.exception(be)
        return response_exception(be)
    except Exception as ex:
        sErrInfo = traceback.format_exc()
        logger.error(sErrInfo)
        dict_resp = {"c": -1, "m": ex.message}
        return HttpResponse(json.dumps(dict_resp, ensure_ascii=False), content_type="application/json")


@validate('GET', auth=True)
def api_get_outsimipic(request):
    try:
        pic_url = getp(request.GET.get('pic_url'), nullable=True, para_intro='外部图片地址')
        file_obj_id = getp(request.GET.get('file_obj_id'), nullable=True, para_intro='文件id')
        activity_id = getp(request.GET.get('activity_id'), nullable=True, para_intro='活动id', default='')

        domain = get_cur_domain(request)
        dict_resp = agents.api_get_outsimipic(domain, pic_url, activity_id, file_obj_id)
        dict_resp = paging_with_request(request, dict_resp)
        log_response(request, dict_resp)
        return HttpResponse(json.dumps(dict_resp, ensure_ascii=False), content_type="application/json")

    except BusinessException as be:
        logger.exception(be)
        return response_exception(be)
    except Exception as ex:
        sErrInfo = traceback.format_exc()
        logger.error(sErrInfo)
        dict_resp = {"c": -1, "m": ex.message}
        return HttpResponse(json.dumps(dict_resp, ensure_ascii=False), content_type="application/json")


@validate('POST', auth=True)
def api_public_work(request):
    try:
        work_id_list = getp(request.POST.get('work_id_list'), nullable=False, para_intro='作品id列表')
        is_public = getp(request.POST.get('is_public'), nullable=False, para_intro='公示状态')  # 1：公示  0：取消公示

        dict_resp = agents.api_public_work(request.user, work_id_list, is_public)
        log_response(request, dict_resp)
        return HttpResponse(json.dumps(dict_resp, ensure_ascii=False), content_type="application/json")

    except BusinessException as be:
        logger.exception(be)
        return response_exception(be)
    except Exception as ex:
        sErrInfo = traceback.format_exc()
        logger.error(sErrInfo)
        dict_resp = {"c": -1, "m": ex.message}
        return HttpResponse(json.dumps(dict_resp, ensure_ascii=False), content_type="application/json")


@validate('GET', auth=False)
def api_list_publicwork(request):
    try:
        activity_id = getp(request.GET.get('activity_id'), nullable=False, para_intro='作品id列表')
        order = getp(request.GET.get('order'), nullable=True, para_intro='排序', default='1')  # 1:按浏览排序，2：按点赞排序
        rows = getp(request.GET.get('rows'), nullable=True, para_intro='一次返回最大行数')
        page = getp(request.GET.get('page'), nullable=True, para_intro='页码')
        last_id = getp(request.GET.get('last_id'), nullable=True, para_intro='最后id')

        dict_resp = agents.api_list_publicwork(request.user, activity_id, order, rows, page, last_id)
        log_response(request, dict_resp)
        return HttpResponse(json.dumps(dict_resp, ensure_ascii=False), content_type="application/json")

    except BusinessException as be:
        logger.exception(be)
        return response_exception(be)
    except Exception as ex:
        sErrInfo = traceback.format_exc()
        logger.error(sErrInfo)
        dict_resp = {"c": -1, "m": ex.message}
        return HttpResponse(json.dumps(dict_resp, ensure_ascii=False), content_type="application/json")


@check('GET', para=(
    {'name': 'work_id'},
))
def api_workflow(request, para):

    try:
        work = Work.objects.filter(id=int(para.work_id)).first()
        if request.user.auth == 0:
            raise BusinessException(ERR_USER_AUTH)
        result = agents.debug_show_workflow(work)
    except Exception as ex:
        logger.exception(ex)
        return response_exception(ex, ex.message)
    return response200({'c': SUCCESS[0], 'm': SUCCESS[1], 'd':result})


@check('GET', para=(
    {'name': 'role_id'},
))
def api_approve_count(request, para):
    try:
        role = Role.objects.filter(id=int(para.role_id)).first()
        if request.user.auth == 0:
            raise BusinessException(ERR_USER_AUTH)
        result = agents.debug_approve_count(role)
    except Exception as ex:
        logger.exception(ex)
        return response_exception(ex, ex.message)
    return response200({'c': SUCCESS[0], 'm': SUCCESS[1], 'd':result})
