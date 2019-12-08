# coding=utf-8
import logging
import os

from django.conf import settings
from django.http import HttpResponse

from applications.activity.models import Activity
from applications.expert.models import Expert
from applications.subjudge.models import SubJudgeTeam, SubJudge, SubJudgeExpert, SubJudgeTeamWork
from applications.user.models import User, Area
from applications.work.export import WorkExcelExport, EXCEL
from applications.work.models import Work
from applications.work.share import get_user
from utils.const_def import FLAG_NO, FLAG_YES, ACTIVITY_STAGE_EDIT, TRUE_STR, FALSE_INT, FALSE_STR
from utils.const_err import SUCCESS, ERR_TEMPLATE_NOT_EXIST, ERR_ACTIVITY_NOT_EXIST, ERR_DEL_FORBIT_1, ERR_SUBJUDGE_NOT_EXIST, ERR_TEAM_EMPTY, ERR_USER_AUTH, \
    ERR_SUBJUDGE_TEAM_NOT_EXIST, ERR_WORK_ID_ERROR
from utils.net_helper import response_parameter_error, response200, response_exception
from utils.check_auth import validate, check
from utils.public_fun import paging_with_request, str_p_datetime, seq2list, suuid
from utils.utils_except import BusinessException
from utils.utils_log import log_response, log_request
from utils.check_param import getp, InvalidHttpParaException
import applications.subjudge.services as subjudge_services

logger = logging.getLogger(__name__)


@check('POST', para=(
    {'name': 'subjudge_id'},
    {'name': 'status'},
))
def api_control_subjudge(request, para):
    try:
        subjudge = SubJudge.objects.filter(id=int(para.subjudge_id)).first()
        if not subjudge:
            raise BusinessException(ERR_SUBJUDGE_NOT_EXIST)

        # 仅子级评审的维护者可使用
        if not subjudge_services.is_subjudge_manager(subjudge, request.user):
            raise BusinessException(ERR_USER_AUTH)

        result = subjudge_services.control(request.user, subjudge, para.status)
    except Exception as e:
        logger.exception(e)
        return response_exception(e)
    return response200({'c': SUCCESS[0], 'm': SUCCESS[1], 'd': result})


@check('POST', para=(
    {'name': 'subjudge_id'},
    {'name': 'sub_activity', 'default': None},   # 过滤条件
    {'name': 'phase', 'default': None},   # 过滤条件
    {'name': 'project', 'default': None},   # 过滤条件
    {'name': 'subject', 'default': None},   # 过滤条件
    {'name': 'keyword', 'default': None},   # 过滤条件
    {'name': 'subjudge_team', 'default': None},   # 过滤条件
    {'name': 'is_unfinish', 'default': None},   # 过滤条件
    {'name': 'page', 'default': '1'},
    {'name': 'rows', 'default': '10'},
))
def api_subjudge_list_work_for_expert(request, para):
    try:
        subjudge = SubJudge.objects.filter(id=int(para.subjudge_id)).first()
        if not subjudge:
            raise BusinessException(ERR_SUBJUDGE_NOT_EXIST)
        subjg_team = SubJudgeTeam.objects.filter(id=int(para.subjudge_team)).first() if para.subjudge_team else None
        subjg_expert = SubJudgeExpert.objects.filter(subjudge=subjudge, expert__account=request.user).first()
        if not subjg_expert:
            raise BusinessException(ERR_USER_AUTH)
        result = subjudge_services.list_work_for_expert(
            request.user, subjudge, subjg_expert, para.sub_activity, para.phase, para.project,
            para.subject, para.keyword, subjg_team, para.is_unfinish, para.page, para.rows,
        )
    except Exception as ex:
        logger.exception(ex)
        return response_exception(ex, ex.message)
    return response200({'c': SUCCESS[0], 'm': SUCCESS[1], 'd':result})


@check('POST', para=(
    {'name': 'subjudge_id'},
    {'name': 'sub_activity', 'default': None},   # 过滤条件
    {'name': 'phase', 'default': None},   # 过滤条件
    {'name': 'project', 'default': None},   # 过滤条件
    {'name': 'subject', 'default': None},   # 过滤条件
    {'name': 'keyword', 'default': None},   # 过滤条件
    {'name': 'subjudge_team', 'default': None},   # 过滤条件
    {'name': 'is_unfinish', 'default': None},   # 过滤条件
    {'name': 'page', 'default': '1'},
    {'name': 'rows', 'default': '10'},
))
def api_subjudge_list_work_for_leader(request, para):
    try:
        subjudge = SubJudge.objects.filter(id=int(para.subjudge_id)).first()
        if not subjudge:
            raise BusinessException(ERR_SUBJUDGE_NOT_EXIST)
        subjg_team = SubJudgeTeam.objects.filter(id=int(para.subjudge_team)).first() if para.subjudge_team else None
        subjg_expert = SubJudgeExpert.objects.filter(subjudge=subjudge, expert__account=request.user).first()
        if not subjg_expert:
            raise BusinessException(ERR_USER_AUTH)
        # 验证必须是组长
        # TODO
        result = subjudge_services.list_work_for_leader(
                request.user, subjudge, subjg_expert, para.sub_activity, para.phase, para.project,
                para.subject, para.keyword, subjg_team, para.is_unfinish, para.page, para.rows,
        )
    except Exception as ex:
        logger.exception(ex)
        return response_exception(ex, ex.message)
    return response200({'c': SUCCESS[0], 'm': SUCCESS[1], 'd':result})


@check('POST', para=(
    {'name': 'subjudge_id'},
    {'name': 'subjudge_team'},
    {'name': 'sub_activity', 'default': None},   # 过滤条件
    {'name': 'phase', 'default': None},   # 过滤条件
    {'name': 'project', 'default': None},   # 过滤条件
    {'name': 'area_id', 'default': None},   # 过滤条件
    {'name': 'direct_area_id', 'default': None},   # 过滤条件
    {'name': 'subject', 'default': None},   # 过滤条件
    {'name': 'keyword', 'default': None},   # 过滤条件
    {'name': 'page', 'default': '1'},
    {'name': 'rows', 'default': '10'},
))
def api_subjudge_work_in_team(request, para):
    try:
        subjudge = SubJudge.objects.filter(id=int(para.subjudge_id)).first()
        if not subjudge:
            raise BusinessException(ERR_SUBJUDGE_NOT_EXIST)
        area = Area.objects.filter(id=int(para.area_id)).first() if para.area_id else None
        direct_area = Area.objects.filter(id=int(para.direct_area_id)).first() if para.direct_area_id else None
        subjudge_team = SubJudgeTeam.objects.filter(id=int(para.subjudge_team)).first()
        if not subjudge_team:
            raise BusinessException(ERR_TEAM_EMPTY)
        result = subjudge_services.work_in_team(
                request.user, subjudge, subjudge_team, para.sub_activity, para.phase,
                para.project, area, direct_area, para.subject, para.keyword,
                para.page, para.rows,
        )
    except Exception as ex:
        logger.exception(ex)
        return response_exception(ex, ex.message)
    return response200({'c': SUCCESS[0], 'm': SUCCESS[1], 'd':result})


@check('POST', para=(
    {'name': 'subjudge_id'},
    {'name': 'subjudge_team'},
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
def api_subjudge_work_availale_add_team(request, para):
    try:
        subjudge = SubJudge.objects.filter(id=int(para.subjudge_id)).first()
        if not subjudge:
            raise BusinessException(ERR_SUBJUDGE_NOT_EXIST)

        # 仅子级评审的维护者可使用
        if not subjudge_services.is_subjudge_manager(subjudge, request.user):
            raise BusinessException(ERR_USER_AUTH)

        area = Area.objects.filter(id=int(para.area_id)).first() if para.area_id else None
        direct_area = Area.objects.filter(id=int(para.direct_area_id)).first() if para.direct_area_id else None
        subjudge_team = SubJudgeTeam.objects.filter(id=int(para.subjudge_team)).first()
        if not subjudge_team:
            raise BusinessException(ERR_TEAM_EMPTY)
        ignore_area_list = para.ignore_area_id.strip().strip(',').split(',') if para.ignore_area_id else []

        result = subjudge_services.work_availale_add_team(
                request.user, subjudge, subjudge_team, para.sub_activity, para.phase,
                para.project, area, direct_area, para.subject, para.keyword, ignore_area_list,
                para.page, para.rows,
        )
    except Exception as e:
        logger.exception(e)
        return response_exception(e)
    return response200({'c': SUCCESS[0], 'm': SUCCESS[1], 'd':result})


@check('POST', para=(
    {'name': 'activity_id'},
    {'name': 'is_active'},
    {'name': 'data', 'default': None},
))
def api_decide_subjudge(request, para):
    try:
        activity = Activity.objects.filter(id=int(para.activity_id)).first()
        if not activity:
            raise BusinessException(ERR_ACTIVITY_NOT_EXIST)
        user, role = get_user(activity, request.user)
        if not user:
            raise BusinessException(ERR_USER_AUTH)
        result = subjudge_services.decide_subjudge(
            request.user, user, role, activity, para.is_active, para.data,)
    except Exception as e:
        logger.exception(e)
        return response_exception(e)
    return response200({'c': SUCCESS[0], 'm': SUCCESS[1], 'd':result})


@check('POST', para=(
    {'name': 'subjudge_id'},
))
def api_detail_subjudge(request, para):
    try:
        subjudge = SubJudge.objects.filter(id=int(para.subjudge_id)).first()
        if not subjudge:
            raise BusinessException(ERR_SUBJUDGE_NOT_EXIST)
        result = subjudge_services.detail_subjudge(subjudge)
    except Exception as e:
        logger.exception(e)
        return response_exception(e)
    return response200({'c': SUCCESS[0], 'm': SUCCESS[1], 'd':result})


@check('POST', para=(
    {'name': 'subjudge_id'},
    {'name': 'expert_id_list'},
))
def api_add_expert(request, para):
    try:
        subjudge = SubJudge.objects.filter(id=int(para.subjudge_id)).first()
        if not subjudge:
            raise BusinessException(ERR_SUBJUDGE_NOT_EXIST)
        expert_id_list = [int(each) for each in seq2list(para.expert_id_list)]

        # 仅子级评审的维护者可使用
        if not subjudge_services.is_subjudge_manager(subjudge, request.user):
            raise BusinessException(ERR_USER_AUTH)

        result = subjudge_services.add_expert(request.user, subjudge, expert_id_list)
    except Exception as e:
        logger.exception(e)
        return response_exception(e)
    return response200({'c': SUCCESS[0], 'm': SUCCESS[1], 'd':result})


@check("POST", para=(
    {'name': 'subjudge_id'},
    {'name': 'mobile'},
    {'name': 'name'},
    {'name': 'sex', 'default': u'男'},
    {'name': 'area_id', 'default': None},
    {'name': 'direct_area_id', 'default': None},
    {'name': 'institution', 'default': None},
    {'name': 'position', 'default': ''},
))
def api_new_expert(request, para):
    try:
        subjudge = SubJudge.objects.filter(id=int(para.subjudge_id)).first()
        if not subjudge:
            raise BusinessException(ERR_SUBJUDGE_NOT_EXIST)
        user, role = get_user(subjudge.activity, request.user)
        if not user:
            raise BusinessException(ERR_USER_AUTH)

        # 仅子级评审的维护者可使用
        if not subjudge_services.is_subjudge_manager(subjudge, request.user):
            raise BusinessException(ERR_USER_AUTH)

        area = Area.objects.filter(del_flag=FLAG_NO, id=int(para.area_id)).first() if para.area_id else None
        direct_area = Area.objects.filter(del_flag=FLAG_NO, id=int(para.direct_area_id)).first() if para.direct_area_id else None
        result = subjudge_services.new_expert(
                request.user, subjudge, user, para.mobile, para.name, para.sex,
                area, direct_area, para.institution, para.position)
    except Exception as ex:
        logger.exception(ex)
        return response_exception(ex)
    return response200(dict(c=SUCCESS[0], m=SUCCESS[1], d=result))


@check('POST', para=(
    {'name': 'subjudge_id'},
    {'name': 'keyword', 'default': None},
    {'name': 'page', 'default': '1'},
    {'name': 'rows', 'default': '10'},
))
def api_list_expert(request, para):
    try:
        subjudge = SubJudge.objects.filter(id=int(para.subjudge_id)).first()
        if not subjudge:
            raise BusinessException(ERR_SUBJUDGE_NOT_EXIST)
        result = subjudge_services.list_expert(request.user, subjudge, para.keyword, para.rows, para.page)
    except Exception as e:
        logger.exception(e)
        return response_exception(e)
    return response200({'c': SUCCESS[0], 'm': SUCCESS[1], 'd':result})


@check('POST', para=(
    {'name': 'subjudge_id'},
    {'name': 'keyword', 'default': None},
    {'name': 'page', 'default': '1'},
    {'name': 'rows', 'default': '10'},
))
def api_available_add_expert(request, para):
    try:
        subjudge = SubJudge.objects.filter(id=int(para.subjudge_id)).first()
        if not subjudge:
            raise BusinessException(ERR_SUBJUDGE_NOT_EXIST)

        # 仅子级评审的维护者可使用
        if not subjudge_services.is_subjudge_manager(subjudge, request.user):
            raise BusinessException(ERR_USER_AUTH)

        result = subjudge_services.available_add_expert(request.user, subjudge, para.keyword, para.rows, para.page)
    except Exception as e:
        logger.exception(e)
        return response_exception(e)
    return response200({'c': SUCCESS[0], 'm': SUCCESS[1], 'd':result})


@check("POST", para=(
    {'name': 'subjudge_id'},
    {'name': 'expert_id_list', 'default': ''},
))
def api_export_expert(request, para):
    try:
        subjudge = SubJudge.objects.filter(id=int(para.subjudge_id)).first()
        if not subjudge:
            raise BusinessException(ERR_SUBJUDGE_NOT_EXIST)
        user, role = get_user(subjudge.activity, request.user)
        if not user:
            raise BusinessException(ERR_USER_AUTH)

        # 仅子级评审的维护者可使用
        if not subjudge_services.is_subjudge_manager(subjudge, request.user):
            raise BusinessException(ERR_USER_AUTH)

        expert_id_list = [int(r) for r in para.expert_id_list.strip().strip(',').split(',')]
        expert_list = Expert.objects.filter(del_flag=FALSE_INT, id__in=expert_id_list)
        import applications.activity.services as activity_s
        wb = activity_s.export_activity_expert(request.user, subjudge.activity, user, role, expert_list)

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


@check("POST", para=(
    {'name': 'subjudge_id'},
    {'name': 'file', 'is_file': True, },
))
def api_import_expert(request, para):
    try:
        subjudge = SubJudge.objects.filter(id=int(para.subjudge_id)).first()
        if not subjudge:
            raise BusinessException(ERR_SUBJUDGE_NOT_EXIST)
        user, role = get_user(subjudge.activity, request.user)
        if not user:
            raise BusinessException(ERR_USER_AUTH)
        # 仅子级评审的维护者可使用
        if not subjudge_services.is_subjudge_manager(subjudge, request.user):
            raise BusinessException(ERR_USER_AUTH)
        result = subjudge_services.import_expert(request.user, user, role, subjudge, para.file)
    except Exception as ex:
        logger.exception(ex)
        return response_exception(ex, ex.message)
    return response200(dict(c=SUCCESS[0], m=SUCCESS[1], d=result))


@check('POST', para=(
    {'name': 'subjudge_id'},
    {'name': 'expert_id_list'},
))
def api_remove_expert(request, para):
    try:
        subjudge = SubJudge.objects.filter(id=int(para.subjudge_id)).first()
        if not subjudge:
            raise BusinessException(ERR_SUBJUDGE_NOT_EXIST)

        # 仅子级评审的维护者可使用
        if not subjudge_services.is_subjudge_manager(subjudge, request.user):
            raise BusinessException(ERR_USER_AUTH)

        expert_id_list = [int(each) for each in seq2list(para.expert_id_list)]
        result = subjudge_services.remove_expert(request.user, subjudge, expert_id_list)
    except Exception as e:
        logger.exception(e)
        return response_exception(e)
    return response200(result)


@check('POST', para=(
    {'name': 'subjudge_id'},
    {'name': 'keyword', 'default': None},
    {'name': 'judger', 'default': None},
    {'name': 'page', 'default': '1'},
    {'name': 'rows', 'default': '10'},
))
def api_list_team(request, para):
    try:
        subjudge = SubJudge.objects.filter(id=int(para.subjudge_id)).first()
        if not subjudge:
            raise BusinessException(ERR_SUBJUDGE_NOT_EXIST)
        # 仅子级评审的维护者可使用
        if not subjudge_services.is_subjudge_manager(subjudge, request.user):
            raise BusinessException(ERR_USER_AUTH)
        result = subjudge_services.list_team(subjudge, para.keyword, para.judger, para.rows, para.page)
    except Exception as e:
        logger.exception(e)
        return response_exception(e)
    return response200({'c': SUCCESS[0], 'm': SUCCESS[1], 'd': result})


@check('POST', para=(
    {'name': 'subjudge_id'},
    {'name': 'as_leader', 'default': '0'},
))
def api_list_team_judger(request, para):
    try:
        subjudge = SubJudge.objects.filter(id=int(para.subjudge_id)).first()
        if not subjudge:
            raise BusinessException(ERR_SUBJUDGE_NOT_EXIST)
        result = subjudge_services.list_team_by_judger(request.user, subjudge, para.as_leader)
    except Exception as e:
        logger.exception(e)
        return response_exception(e)
    return response200({'c': SUCCESS[0], 'm': SUCCESS[1], 'd': result})


@check('POST', para=(
    {'name': 'subjudge_id'},
    {'name': 'subjudge_team', 'default':None},
    {'name': 'new_name'},
))
def api_edit_team(request, para):
    try:
        subjudge = SubJudge.objects.filter(id=int(para.subjudge_id)).first()
        if not subjudge:
            raise BusinessException(ERR_SUBJUDGE_NOT_EXIST)

        # 仅子级评审的维护者可使用
        if not subjudge_services.is_subjudge_manager(subjudge, request.user):
            raise BusinessException(ERR_USER_AUTH)

        subjudge_team = SubJudgeTeam.objects.filter(
                    id=int(para.subjudge_team)).first() if para.subjudge_team else None
        result = subjudge_services.edit_team(subjudge, subjudge_team, para.new_name)
    except Exception as e:
        logger.exception(e)
        return response_exception(e)
    return response200({'c': SUCCESS[0], 'm': SUCCESS[1], 'd': result})


@check('POST', para=(
    {'name': 'subjudge_team_list'},
))
def api_delete_team(request, para):
    try:
        subjudge_teams = [int(each) for each in seq2list(para.subjudge_team_list)]
        subjudge_team_obj_list = SubJudgeTeam.objects.filter(id__in=subjudge_teams)
        result = subjudge_services.delete_team(request.user, subjudge_team_obj_list)
    except Exception as e:
        logger.exception(e)
        return response_exception(e)
    return response200({'c': SUCCESS[0], 'm': SUCCESS[1], 'd': result})


@check('POST', para=(
    {'name': 'subjudge_team'},
    {'name': 'work_id_list'},
))
def api_add_team_work(request, para):
    try:
        subjudge_team = SubJudgeTeam.objects.filter(id=int(para.subjudge_team)).first()
        if not subjudge_team:
            raise BusinessException(ERR_SUBJUDGE_TEAM_NOT_EXIST)

        # 仅子级评审的维护者可使用
        if not subjudge_services.is_subjudge_manager(subjudge_team.subjudge, request.user):
            raise BusinessException(ERR_USER_AUTH)

        work_id_list = [int(each) for each in para.work_id_list.strip().strip(',').split(',') if each]
        result = subjudge_services.add_team_work(subjudge_team, work_id_list)
    except Exception as e:
        logger.exception(e)
        return response_exception(e)
    return response200({'c': SUCCESS[0], 'm': SUCCESS[1], 'd': result})


@check('POST', para=(
    {'name': 'subjudge_team'},
    {'name': 'work_id_list'},
))
def api_remove_team_work(request, para):
    try:
        subjudge_team = SubJudgeTeam.objects.filter(id=int(para.subjudge_team)).first()
        if not subjudge_team:
            raise BusinessException(ERR_SUBJUDGE_TEAM_NOT_EXIST)

        # 仅子级评审的维护者可使用
        if not subjudge_services.is_subjudge_manager(subjudge_team.subjudge, request.user):
            raise BusinessException(ERR_USER_AUTH)

        work_id_list = [int(each) for each in para.work_id_list.strip().strip(',').split(',') if each]
        result = subjudge_services.remove_team_work(subjudge_team, work_id_list)
    except Exception as e:
        logger.exception(e)
        return response_exception(e)
    return response200({'c': SUCCESS[0], 'm': SUCCESS[1], 'd': result})


@check('POST', para=(
    {'name': 'subjudge_id'},
    {'name': 'subjudge_team_list'},
))
def api_export_team(request, para):
    try:
        subjudge = SubJudge.objects.filter(id=int(para.subjudge_id)).first()
        if not subjudge:
            raise BusinessException(ERR_SUBJUDGE_NOT_EXIST)
        user, role = get_user(subjudge.activity, request.user)
        if not user:
            raise BusinessException(ERR_USER_AUTH)
        # 仅子级评审的维护者可使用
        if not subjudge_services.is_subjudge_manager(subjudge, request.user):
            raise BusinessException(ERR_USER_AUTH)
        subjudge_team_id_list = [int(each) for each in para.subjudge_team_list.strip().strip(',').split(',') if each]
        # team_list = list(Team.objects.filter(id__in=team_id_list))
        wb = subjudge_services.export_team(request.user, subjudge, user, role, subjudge_team_id_list)

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
        return response_exception(ex)


@check('POST', para=(
    {'name': 'subjudge_team', 'default':None},
))
def api_detail_team(request, para):
    try:
        subjudge_team = SubJudgeTeam.objects.filter(id=int(para.subjudge_team)).first()
        if not subjudge_team:
            raise BusinessException(ERR_SUBJUDGE_TEAM_NOT_EXIST)
        result = subjudge_services.detail_team(subjudge_team)
    except Exception as e:
        logger.exception(e)
        return response_exception(e)
    return response200({'c': SUCCESS[0], 'm': SUCCESS[1], 'd': result})


@check('POST', para=(
    {'name': 'subjudge_team'},
    {'name': 'data'},
))
def api_update_team_expert(request, para):
    try:
        subjudge_team = SubJudgeTeam.objects.filter(id=int(para.subjudge_team)).first()
        if not subjudge_team:
            raise BusinessException(ERR_SUBJUDGE_TEAM_NOT_EXIST)

        # 仅子级评审的维护者可使用
        if not subjudge_services.is_subjudge_manager(subjudge_team.subjudge, request.user):
            raise BusinessException(ERR_USER_AUTH)

        result = subjudge_services.update_team_expert(subjudge_team, para.data)
    except Exception as e:
        logger.exception(e)
        return response_exception(e)
    return response200({'c': SUCCESS[0], 'm': SUCCESS[1], 'd': result})


@check('POST', para=(
    {'name': 'subjudge_team'},
    {'name': 'keyword', 'default': None},
    {'name': 'expert_in_same_team', 'default': list()},
    {'name': 'page', 'default': '1'},
    {'name': 'rows', 'default': '10'},
))
def api_available_add_team_expert(request, para):
    try:
        subjudge_team = SubJudgeTeam.objects.filter(id=int(para.subjudge_team)).first()
        if not subjudge_team:
            raise BusinessException(ERR_SUBJUDGE_TEAM_NOT_EXIST)

        # 仅子级评审的维护者可使用
        if not subjudge_services.is_subjudge_manager(subjudge_team.subjudge, request.user):
            raise BusinessException(ERR_USER_AUTH)

        result = subjudge_services.available_add_team_expert(subjudge_team, para.expert_in_same_team, para.keyword, para.page, para.rows)
    except Exception as e:
        logger.exception(e)
        return response_exception(e)
    return response200({'c': SUCCESS[0], 'm': SUCCESS[1], 'd': result})


@check('POST', para=(
    {'name': 'subjudge_team'},
))
def api_area_stats_team_expert(request, para):
    # 该子级评审专家组中各个专家都来自于哪一个地区
    try:
        subjudge_team = SubJudgeTeam.objects.filter(id=int(para.subjudge_team)).first()
        if not subjudge_team:
            raise BusinessException(ERR_SUBJUDGE_TEAM_NOT_EXIST)
        user, role = get_user(subjudge_team.subjudge.activity, request.user)
        if not user:
            raise BusinessException(ERR_USER_AUTH)
        result = subjudge_services.area_stats_team_expert(subjudge_team, user, role)
    except Exception as e:
        logger.exception(e)
        return response_exception(e)
    return response200({'c': SUCCESS[0], 'm': SUCCESS[1], 'd': result})


@check('POST', para=(
    {'name': 'subjudge_id'},
    {'name': 'work_id'},
    {'name': 'data', 'default': ''},
    {'name': 'is_submit', 'default': FALSE_INT},
))
def api_edit_score(request, para):
    try:
        subjudge = SubJudge.objects.filter(id=int(para.subjudge_id)).first()
        if not subjudge:
            raise BusinessException(ERR_SUBJUDGE_NOT_EXIST)
        subjudge_team_work = SubJudgeTeamWork.objects.filter(subjudge=subjudge, work__id=int(para.work_id)).first()
        if not subjudge_team_work:
            raise BusinessException(ERR_WORK_ID_ERROR)
        result = subjudge_services.score(request.user, subjudge, subjudge_team_work, para.data, para.is_submit)
    except Exception as e:
        logger.exception(e)
        return response_exception(e)
    return response200({'c': SUCCESS[0], 'm': SUCCESS[1], 'd': result})


@check('POST', para=(
    {'name': 'subjudge_id'},
    {'name': 'work_id'},
    {'name': 'all', 'default': FALSE_STR},
))
def api_detail_score(request, para):
    try:
        subjudge = SubJudge.objects.filter(id=int(para.subjudge_id)).first()
        if not subjudge:
            raise BusinessException(ERR_SUBJUDGE_NOT_EXIST)
        subjudge_team_work = SubJudgeTeamWork.objects.filter(subjudge=subjudge, work__id=int(para.work_id)).first()
        if not subjudge_team_work:
            raise BusinessException(ERR_WORK_ID_ERROR)
        if para.all == FALSE_STR:
            result = subjudge_services.get_score(request.user, subjudge, subjudge_team_work)
        else:
            result = subjudge_services.load_all_score(request.user, subjudge, subjudge_team_work)
    except Exception as e:
        logger.exception(e)
        return response_exception(e)
    return response200({'c': SUCCESS[0], 'm': SUCCESS[1], 'd': result})


@check('POST', para=(
    {'name': 'subjudge_id'},
    {'name': 'score_id_list'},
))
def api_submit_score(request, para):
    try:
        subjudge = SubJudge.objects.filter(id=int(para.subjudge_id)).first()
        if not subjudge:
            raise BusinessException(ERR_SUBJUDGE_NOT_EXIST)
        id_list = para.score_id_list.strip().strip(',').split(',')
        result = subjudge_services.submit_score(request.user, subjudge, id_list)
    except Exception as e:
        logger.exception(e)
        return response_exception(e)
    return response200({'c': SUCCESS[0], 'm': SUCCESS[1], 'd': result})


@check('POST', para=(
    {'name': 'subjudge_id'},
    {'name': 'work_id_list'},
))
def api_subjudge_export_work_for_expert(request, para):
    try:
        subjudge = SubJudge.objects.filter(id=int(para.subjudge_id)).first()
        if not subjudge:
            raise BusinessException(ERR_SUBJUDGE_NOT_EXIST)
        subj_expert = SubJudgeExpert.objects.filter(subjudge=subjudge, expert__del_flag=FALSE_INT, expert__account=request.user).first()
        if not subj_expert:
            raise BusinessException(ERR_USER_AUTH)
        work_id_list = [int(each) for each in para.work_id_list.strip().strip(',').split(',') if each]
        work_list = list(Work.objects.filter(id__in=work_id_list))

        # TODO check auth for these work
        #

        resp = WorkExcelExport(subjudge.activity, work_list,
                (EXCEL.BASIC, EXCEL.AUTHOR, EXCEL.TUTOR, EXCEL.SUBJG_MY_SCORE), expert=subj_expert.expert, subjudge=subjudge)\
                .write().dump_stream()
        return resp
    except Exception as ex:
        logger.exception(ex)
        return response_exception(ex, ex.message)


@check('POST', para=(
    {'name': 'subjudge_id'},
    {'name': 'work_id_list'},
))
def api_subjudge_export_work_for_leader(request, para):
    try:
        subjudge = SubJudge.objects.filter(id=int(para.subjudge_id)).first()
        if not subjudge:
            raise BusinessException(ERR_SUBJUDGE_NOT_EXIST)
        subj_expert = SubJudgeExpert.objects.filter(subjudge=subjudge, expert__del_flag=FALSE_INT, expert__account=request.user).first()
        if not subj_expert:
            raise BusinessException(ERR_USER_AUTH)
        # TODO 验证必须是组长
        #

        work_id_list = [int(each) for each in para.work_id_list.strip().strip(',').split(',') if each]
        work_list = list(Work.objects.filter(id__in=work_id_list))

        # TODO check auth for these work
        #

        resp = WorkExcelExport(subjudge.activity, work_list,
                (EXCEL.BASIC, EXCEL.AUTHOR, EXCEL.TUTOR, EXCEL.SUBJG_MY_SCORE, EXCEL.SUBJG_SCORE), expert=subj_expert.expert, subjudge=subjudge)\
                .write().dump_stream()
        return resp
    except Exception as ex:
        logger.exception(ex)
        return response_exception(ex, ex.message)




