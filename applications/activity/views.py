# coding=utf-8
import time
import json
import logging
import os
from django.conf import settings
from django.db import transaction
from django.db.models import F
from django.http import HttpResponse
from django.core.cache import cache
from applications.activity.models import Activity, Role
from applications.activity.share import is_activity_owner, is_devops, subordinate_area_level
from applications.expert.models import Expert
from applications.user.models import User, Area
from applications.work.share import get_user
from utils.const_def import FLAG_NO, FLAG_YES, ACTIVITY_STAGE_EDIT, TRUE_STR, FALSE_STR, ACTIVITY_STAGE_UPLOAD, ACTIVITY_STAGE_GROUP, ACTIVITY_STAGE_REVIEW, ACTIVITY_STAGE_PUBLIC
from utils.const_err import SUCCESS, ERR_TEMPLATE_NOT_EXIST, ERR_ACTIVITY_NOT_EXIST, ERR_DEL_FORBIT_1, ERR_USER_NOT_EXIST, ERR_TIME_AHEAD, ERR_AREA_ERROR, ERR_USER_AUTH
from utils.ipware import get_client_ip
from utils.net_helper import response200, response_exception
from utils.check_auth import validate, check
from utils.public_fun import paging_with_request, str_p_datetime, suuid
from utils.utils_except import BusinessException
from utils.utils_log import log_response, log_request
import applications.activity.services as activity_s
from utils.utils_type import str2bool

logger = logging.getLogger(__name__)


def _check_activity_time(para):
    tlist = (str_p_datetime(para.start_time),
             str_p_datetime(para.upload_time),
             str_p_datetime(para.group_time),
             str_p_datetime(para.review_time),
             str_p_datetime(para.public_time),
             str_p_datetime(para.archive_time),)
    for i, t in enumerate(tlist):
        for i in xrange(i+1, len(tlist)):
            if t and tlist[i] and tlist[i] <= t:
                raise BusinessException(ERR_TIME_AHEAD)


@check("POST")
def api_list_activity_create_area(request):
    try:
        result = activity_s.list_activity_create_area(request.user)
    except Exception as ex:
        logger.exception(ex)
        return response_exception(ex, ex.message)
    return response200(result)


@check("POST", para=(
    {'name': 'category_list', 'default': None},
))
def api_list_activity_category(request, para):
    try:
        result = activity_s.list_activity_category(request.user, para.category_list)
    except Exception as ex:
        logger.exception(ex)
        return response_exception(ex, ex.message)
    return response200(dict(c=SUCCESS[0], m=SUCCESS[1], d=result))


@check('POST', para=(
    {'name': 'activity_id'},

    {'name': 'start_time', 'default': None},
    {'name': 'upload_time', 'default': None},
    {'name': 'group_time', 'default': None},
    {'name': 'review_time', 'default': None},
    {'name': 'public_time', 'default': None},
    {'name': 'archive_time', 'default': None},

    {'name': 'name', 'default': None},
    {'name': 'organizer', 'default': None},
    {'name': 'participator', 'default': None},
    {'name': 'banner_id', 'default': None},
    {'name': 'attachment_id', 'default': None},
    {'name': 'introduction', 'default': None},
    {'name': 'base_info_value', 'default': None},
    {'name': 'stage', 'default': None},
    {'name': 'author_count', 'default': None},
    {'name': 'tutor_count', 'default': None},
    {'name': 'copyright', 'default': None},
    {'name': 'is_top', 'default': None},
    {'name': 'is_minor', 'default': None},
    {'name': 'genre', 'default': None},
))
def api_edit_activity(request, para):
    # 修改模板  修改活动  切换活动阶段
    try:
        # 检查时间先后有效性
        _check_activity_time(para)

        result = activity_s.edit_activity(
            request.user, para.name, para.activity_id, para.stage,
            para.start_time, para.upload_time, para.group_time, para.review_time, para.public_time, para.archive_time,
            para.organizer, para.participator, para.banner_id, para.attachment_id,
            para.introduction, para.author_count, para.tutor_count,
            para.base_info_value, para.copyright, para.is_top, para.is_minor, para.genre )
    except Exception as ex:
        logger.exception(ex)
        return response_exception(ex, ex.message)
    return response200({'c': SUCCESS[0], 'm': SUCCESS[1], 'd': result})


@check("POST", auth=False, para=(
    {'name': 'activity_id'},
))
def api_detail_work_attr(request, para):
    activity = Activity.objects.filter(pk=int(para.activity_id)).first()
    if not activity:
        raise BusinessException(ERR_ACTIVITY_NOT_EXIST)
    try:
        result = activity_s.detail_work_attr(activity)
    except Exception as ex:
        logger.exception(ex)
        return response_exception(ex, ex.message)
    return response200(result)


@check("POST", auth=False, para=(
    {'name': 'activity_id'},
))
def api_detail_work_attr_schema(request, para):
    activity = Activity.objects.filter(pk=int(para.activity_id)).first()
    if not activity:
        raise BusinessException(ERR_ACTIVITY_NOT_EXIST)
    try:
        result = activity_s.detail_work_attr_schema(activity)
    except Exception as ex:
        logger.exception(ex)
        return response_exception(ex, ex.message)
    return response200(result)


# @check("POST", para=(
#     {'name': 'activity_id'},
#     {'name': 'category'},
#     {'name': 'work_attr_list'},
#     {'name': 'count', 'default': 1},    # 重复多少次
# ))
# def api_edit_work_attr_schema(request, para):
#     try:
#         activity = Activity.objects.filter(id=para.activity_id).first()
#         if not activity:
#             raise BusinessException(ERR_ACTIVITY_NOT_EXIST)
#         user_obj, role = get_user(activity, request.user)
#         work_attr_list = json.loads(para.work_info_list) if para.work_info_list else []
#         result = activity_s.edit_work_attr(request.user, activity, para.category, work_attr_list, para.count)
#     except Exception as ex:
#         logger.exception(ex)
#         return response_exception(ex, ex.message)
#     return response200(result)


@check("POST", para=(
    {'name': 'activity_id'},
    {'name': 'bulk_list'}
))
def api_edit_work_attr_schema_bulk(request, para):
    # 一次性更新三类活动信息
    try:
        result = activity_s.edit_work_attr_schema_bulk(request.user, int(para.activity_id), para.bulk_list)
    except Exception as ex:
        logger.exception(ex)
        return response_exception(ex, ex.message)
    return response200(result)


@check("POST", para=(
    {'name': 'activity_id'},
    {'name': 'ranks_list', 'default': None},
))
def api_edit_ranks(request, para):
    try:
        activity = Activity.objects.filter(id=para.activity_id).first()
        if not activity:
            raise BusinessException(ERR_ACTIVITY_NOT_EXIST)
        result = activity_s.edit_ranks(request.user, activity, para.ranks_list)
    except Exception as ex:
        logger.exception(ex)
        return response_exception(ex, ex.message)
    return response200(result)


@check("POST", para=(
    {'name': 'activity_id'},
    {'name': 'rule', 'default': None},
))
def api_edit_rule(request, para):
    try:
        activity = Activity.objects.filter(id=para.activity_id).first()
        if not activity:
            raise BusinessException(ERR_ACTIVITY_NOT_EXIST)
        result = activity_s.edit_rule(request.user, activity, para.rule)
    except Exception as ex:
        logger.exception(ex)
        return response_exception(ex, ex.message)
    return response200(result)


@check("POST", auth=False, para=(
    {'name': 'activity_id'},
))
def api_detail_rule(request, para):
    try:
        activity = Activity.objects.filter(id=para.activity_id).first()
        if not activity:
            raise BusinessException(ERR_ACTIVITY_NOT_EXIST)
        result = activity_s.detail_rule(activity)
    except Exception as ex:
        logger.exception(ex)
        return response_exception(ex, ex.message)
    return response200(result)


@check("POST", auth=False, para=(
    {'name': 'stages', 'default': '%s, %s, %s, %s' %
                (ACTIVITY_STAGE_UPLOAD, ACTIVITY_STAGE_GROUP, ACTIVITY_STAGE_REVIEW, ACTIVITY_STAGE_PUBLIC)},
    {'name': 'is_home', 'default': '0'},
    {'name': 'level', 'default': ''},
    {'name': 'rows', 'default': '10'},
    {'name': 'page', 'default': '1'},
))
def api_list_activity(request, para):
    try:
        result = activity_s.all_activity(para.stages, para.is_home, para.level, para.rows, para.page)
    except Exception as ex:
        logger.exception(ex)
        return response_exception(ex, ex.message)
    return response200(result)


def _update_activity_browse_count(request, activity):
    # 统计访问次数
    if request.user.is_anonymous():
        key, is_routable = get_client_ip(request)
    else:
        key = str(request.user.id)
    hit = True
    if not cache.get(key):
        hit = False
    else:
        timestp = cache.get(key)
        now = int(time.time())
        if (now - timestp) > 60 * 5:  # sec
            hit = False
    if not hit:
        logger.info('account %s browse activity %s' % (key, activity.id))
        activity.browse_count = F('browse_count') + 1
        activity.save()
        cache.set(key, int(time.time()))


@check("POST", auth=False, para=(
    {'name': 'activity_id'},
    {'name': 'is_browse', 'default': FALSE_STR},
    {'name': 'with_introduction', 'default': FALSE_STR},
))
def api_detail_activity(request, para):
    with transaction.atomic():
        try:
            activity = Activity.objects.select_for_update().filter(id=int(para.activity_id)).first()
            if not activity:
                raise BusinessException(ERR_ACTIVITY_NOT_EXIST)
            # _update_activity_browse_count(request, activity)
            if str(para.is_browse) == TRUE_STR:
                current_count = activity.browse_count
                activity.browse_count = current_count + 1
                activity.save()

            result = activity_s.detail_activity(request.user, activity, para.with_introduction)
        except Exception as ex:
            logger.exception(ex)
            return response_exception(ex, ex.message)
        return response200(result)


@check("POST", para=(
    {'name': 'activity_id'},
))
def api_delete_activity(request, para):
    try:
        activity = Activity.objects.filter(id=int(para.activity_id), template_flag=FLAG_NO, user__account=request.user).first()
        if not activity:
            raise BusinessException(ERR_ACTIVITY_NOT_EXIST)
        if ACTIVITY_STAGE_EDIT != activity.stage:
            raise BusinessException(ERR_DEL_FORBIT_1)
        result = activity_s.del_activity(activity)
    except Exception as ex:
        logger.exception(ex)
        return response_exception(ex)
    return response200(dict(c=SUCCESS[0], m=SUCCESS[1], d=result))


@check("POST", auth=False, para=(
    {'name': 'activity_id'},
))
def api_detail_ranks(request, para):
    try:
        activity = Activity.objects.filter(id=int(para.activity_id)).first()
        if not activity:
            raise BusinessException(ERR_ACTIVITY_NOT_EXIST)
        result = activity_s.detail_ranks(activity, request.user)
    except Exception as ex:
        logger.exception(ex)
        return response_exception(ex, ex.message)
    return response200(result)


@check("POST", para=(
    {'name': 'activity_id'},
    {'name': 'mobile'},
    {'name': 'name'},
    {'name': 'sex', 'default': u'男'},
    {'name': 'area_id', 'default': None},
    {'name': 'direct_area_id', 'default': None},
    {'name': 'institution', 'default': None},
    {'name': 'max_work', 'default': ''},
))
def api_add_activity_role_new(request, para):
    try:
        activity = Activity.objects.filter(id=int(para.activity_id)).first()
        if not activity:
            raise BusinessException(ERR_ACTIVITY_NOT_EXIST)
        area = Area.objects.filter(id=int(para.area_id)).first() if para.area_id else None
        direct_area = Area.objects.filter(id=int(para.direct_area_id)).first() if para.direct_area_id else None
        user, role = get_user(activity, request.user)
        if not user:
            raise BusinessException(ERR_USER_AUTH)
        result = activity_s.add_activity_role_new(request.user, activity, user, para.mobile, para.name,
                        para.sex, area, direct_area, para.institution, para.max_work)
    except Exception as ex:
        logger.exception(ex)
        return response_exception(ex, ex.message)
    return response200(result)


@check("POST", para=(
    {'name': 'activity_id'},
    {'name': 'file', 'is_file': True, },
))
def api_add_activity_role_import(request, para):
    try:
        activity = Activity.objects.filter(id=int(para.activity_id)).first()
        if not activity:
            raise BusinessException(ERR_ACTIVITY_NOT_EXIST)
        user, role = get_user(activity, request.user)
        if not user:
            raise BusinessException(ERR_USER_AUTH)
        result = activity_s.import_activity_role(request.user, user, role, activity, para.file)
    except Exception as ex:
        logger.exception(ex)
        return response_exception(ex, ex.message)
    return response200(dict(c=SUCCESS[0], m=SUCCESS[1], d=result))


@check("POST", para=(
    {'name': 'activity_id'},
    {'name': 'role_id_list', 'default': ''},
))
def api_export_activity_role(request, para):
    try:
        activity = Activity.objects.filter(id=int(para.activity_id)).first()
        if not activity:
            raise BusinessException(ERR_ACTIVITY_NOT_EXIST)
        user, role = get_user(activity, request.user)
        if not user:
            raise BusinessException(ERR_USER_AUTH)
        role_id_list = [int(r) for r in para.role_id_list.strip().strip(',').split(',')]
        role_list = list(Role.objects.filter(id__in=role_id_list))
        wb = activity_s.export_activity_role(request.user, activity, user, role, role_list)

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
    {'name': 'activity_id'},
))
def api_download_activity_role_template(request, para):
    try:
        activity = Activity.objects.filter(id=int(para.activity_id)).first()
        if not activity:
            raise BusinessException(ERR_ACTIVITY_NOT_EXIST)
        user, role = get_user(activity, request.user)
        if not user:
            raise BusinessException(ERR_USER_AUTH)
        wb = activity_s.download_activity_role_template(request.user, activity, user, role)

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
    {'name': 'activity_id'},
    {'name': 'account_id_list', 'default': 'None'},
    # {'name': 'keyword', 'default': None},
    # {'name': 'all', 'default': FALSE_STR},
))
def api_add_activity_role_registered(request, para):
    activity = Activity.objects.filter(id=int(para.activity_id)).first()
    if not activity:
        raise BusinessException(ERR_ACTIVITY_NOT_EXIST)
    user, role = get_user(activity, request.user)
    if not user:
        raise BusinessException(ERR_USER_AUTH)
    try:
        account_id_list = para.account_id_list.strip().strip(',').split(',')
        result = activity_s.add_activity_role_registered(request.user, activity, user, account_id_list)
    except Exception as ex:
        logger.exception(ex)
        return response_exception(ex, ex.message)
    return response200(result)


@check("POST", para=(
    {'name': 'activity_id'},
    {'name': 'user_id_list', 'default': None},
    # {'name': 'keyword', 'default': None},
    # {'name': 'all', 'default': FALSE_STR},
    # {'name': 'account_id_list', 'default': 'None'},
))
def api_add_activity_role_exist(request, para):
    activity = Activity.objects.filter(id=int(para.activity_id)).first()
    if not activity:
        raise BusinessException(ERR_ACTIVITY_NOT_EXIST)
    user, role = get_user(activity, request.user)
    if not user:
        raise BusinessException(ERR_USER_AUTH)
    try:
        user_id_list = para.user_id_list.strip().strip(',').split(',')
        result = activity_s.add_activity_role_exist(request.user, activity, user, user_id_list)
    except Exception as ex:
        logger.exception(ex)
        return response_exception(ex, ex.message)
    return response200(result)


@check("POST", para=(
    {'name': 'activity_id'},
    {'name': 'all', 'default': FALSE_STR},   # 是否查赛事全局用户，仅创建者可查
    {'name': 'keyword', 'default': None},
    {'name': 'area_id', 'default': None},
    {'name': 'direct_area_id', 'default': None},
    {'name': 'rows', 'default': 10},
    {'name': 'page', 'default': 1},
))
def api_list_activity_role(request, para):
    try:
        activity = Activity.objects.filter(id=int(para.activity_id)).first()
        if not activity:
            raise BusinessException(ERR_ACTIVITY_NOT_EXIST)
        user, role = get_user(activity, request.user)
        if not user:
            raise BusinessException(ERR_USER_AUTH)
        area = Area.objects.filter(del_flag=FLAG_NO, id=int(para.area_id)).first() if para.area_id else None
        d_area = Area.objects.filter(del_flag=FLAG_NO, id=int(para.direct_area_id)).first() if para.direct_area_id else None
        result = activity_s.list_role_in_activity(
            request.user, activity, user, role, para.keyword, area, d_area,
            str2bool(para.all), para.rows, para.page)
    except Exception as ex:
        logger.exception(ex)
        return response_exception(ex, ex.message)
    return response200({'c': SUCCESS[0], 'm': SUCCESS[1], 'd':result})


@check("POST", para=(
    {'name': 'keyword', 'default': None},
    {'name': 'activity_id', 'default': None},
    {'name': 'page', 'default': '1'},
    {'name': 'rows', 'default': '10'},
))
def api_available_user_add_role(request, para):
    # 找出用户库中尚可添加到活动中的人
    try:
        activity = Activity.objects.filter(id=int(para.activity_id)).first()
        if not activity:
            raise BusinessException(ERR_ACTIVITY_NOT_EXIST)
        user, role = get_user(activity, request.user)
        if not user:
            raise BusinessException(ERR_USER_AUTH)
        result = activity_s.available_user_add_role(request.user, user, role, activity, para.keyword, para.page, para.rows)
    except Exception as ex:
        logger.exception(ex)
        return response_exception(ex, ex.message)
    return response200({'c': SUCCESS[0], 'm': SUCCESS[1], 'd': result})


@check("POST", para=(
    {'name': 'activity_id'},
    {'name': 'keyword', 'default': None},
    {'name': 'page', 'default': '1'},
    {'name': 'rows', 'default': '10'},
))
def api_available_registered_add_role(request, para):
    try:
        activity = Activity.objects.filter(id=int(para.activity_id)).first()
        if not activity:
            raise BusinessException(ERR_ACTIVITY_NOT_EXIST)
        user, role = get_user(activity, request.user)
        if not user:
            raise BusinessException(ERR_USER_AUTH)
        result = activity_s.available_registered_add_role(request.user, user, role, activity, para.keyword, para.page, para.rows)
    except Exception as ex:
        logger.exception(ex)
        return response_exception(ex, ex.message)
    return response200({'c': SUCCESS[0], 'm': SUCCESS[1], 'd': result})


@check("POST", para=(
    {'name': 'activity_id'},
    {'name': 'role_id_list', 'default': ''},
))
def api_remove_activity_role(request, para):
    try:
        activity = Activity.objects.filter(id=int(para.activity_id)).first()
        if not activity:
            raise BusinessException(ERR_ACTIVITY_NOT_EXIST)
        user, role = get_user(activity, request.user)
        if not user:
            raise BusinessException(ERR_USER_AUTH)
        result = activity_s.remove_activity_role(
            request.user, activity, role, [int(r) for r in para.role_id_list.strip().strip(',').split(',')])
    except Exception as ex:
        logger.exception(ex)
        return response_exception(ex, ex.message)
    return response200(result)


@check("POST", para=(
    {'name': 'role_id'},
    {'name': 'new_username', 'default': None},
    {'name': 'new_name', 'default': None},
    {'name': 'new_sex', 'default': None},
    {'name': 'new_max', 'default': None},
))
def api_edit_activity_role(request, para):
    try:
        modify_role = Role.objects.filter(id=int(para.role_id)).first()
        if not modify_role:
            raise BusinessException(ERR_ACTIVITY_NOT_EXIST)
        activity = modify_role.activity
        user, role = get_user(activity, request.user)
        if not user:
            raise BusinessException(ERR_USER_AUTH)

        # 非活动创建者则只能修改自己加入的用户（Role）
        if not is_activity_owner(activity, request.user):
            if (not role) or (modify_role.parent_role != role):
                raise BusinessException(ERR_USER_AUTH)

        result = activity_s.edit_activity_role(activity, user, role, modify_role, para.new_username, para.new_name, para.new_sex, para.new_max)
    except Exception as ex:
        logger.exception(ex)
        return response_exception(ex, ex.message)
    return response200({'c': SUCCESS[0], 'm': SUCCESS[1], 'd': result})


@check("POST", para=(
    {'name': 'role_id'},
))
def api_detail_activity_role(request, para):
    try:
        role_retrieved = Role.objects.filter(id=int(para.role_id)).first()
        if not role_retrieved:
            raise BusinessException(ERR_USER_NOT_EXIST)
        user, role = get_user(role_retrieved.activity, request.user)
        if (not user) or (not role):
            raise BusinessException(ERR_USER_AUTH)

        result = activity_s.detail_activity_role(role_retrieved.activity, user, role, role_retrieved)
    except Exception as e:
        logger.exception(e)
        return response_exception(e)
    return response200({'c': SUCCESS[0], 'm': SUCCESS[1], 'd': result})


@check("POST", para=(
    {'name': 'activity_id'},
    {'name': 'expert_id_list', 'default': ''},
))
def api_add_activity_expert_exist(request, para):
    try:
        activity = Activity.objects.filter(id=int(para.activity_id)).first()
        if not activity:
            raise BusinessException(ERR_ACTIVITY_NOT_EXIST)
        user, role = get_user(activity, request.user)
        if not user:
            raise BusinessException(ERR_USER_AUTH)
        result = activity_s.add_activity_expert_exist(
                request.user, activity, user, [int(e) for e in para.expert_id_list.strip().strip(',').split(',')])
    except Exception as ex:
        logger.exception(ex)
        return response_exception(ex, ex.message)
    return response200(result)


@check("POST", para=(
    {'name': 'activity_id'},
    {'name': 'mobile'},
    {'name': 'name'},
    {'name': 'sex', 'default': u'男'},
    {'name': 'area_id', 'default': None},
    {'name': 'direct_area_id', 'default': None},
    {'name': 'institution', 'default': None},
    {'name': 'position', 'default': ''},
))
def api_add_activity_expert_new(request, para):
    try:
        activity = Activity.objects.filter(id=int(para.activity_id)).first()
        if not activity:
            raise BusinessException(ERR_ACTIVITY_NOT_EXIST)
        user, role = get_user(activity, request.user)
        if not user:
            raise BusinessException(ERR_USER_AUTH)
        area = Area.objects.filter(del_flag=FLAG_NO, id=int(para.area_id)).first() if para.area_id else None
        direct_area = Area.objects.filter(del_flag=FLAG_NO, id=int(para.direct_area_id)).first() if para.direct_area_id else None
        result = activity_s.add_activity_expert_new(
                request.user, activity, user, para.mobile, para.name, para.sex,
                area, direct_area, para.institution, para.position)
    except Exception as ex:
        logger.exception(ex)
        return response_exception(ex)
    return response200(dict(c=SUCCESS[0], m=SUCCESS[1], d=result))


@check("POST", para=(
    {'name': 'activity_id'},
    {'name': 'file', 'is_file': True, },
))
def api_import_activity_expert(request, para):
    try:
        activity = Activity.objects.filter(id=int(para.activity_id)).first()
        if not activity:
            raise BusinessException(ERR_ACTIVITY_NOT_EXIST)
        user, role = get_user(activity, request.user)
        if not user:
            raise BusinessException(ERR_USER_AUTH)
        result = activity_s.import_activity_expert(request.user, user, role, activity, para.file)
    except Exception as ex:
        logger.exception(ex)
        return response_exception(ex, ex.message)
    return response200(dict(c=SUCCESS[0], m=SUCCESS[1], d=result))


@check("POST", para=(
    {'name': 'activity_id'},
    {'name': 'keyword', 'default': ''},
    # {'name': 'area_id', 'default': ''},
    # {'name': 'direct_base', 'default': ''},
    # {'name': 'direct_level', 'default': ''},
    # {'name': 'institution', 'default': ''},
    {'name': 'rows', 'default': 10},
    {'name': 'page', 'default': 1},
))
def api_list_activity_expert(request, para):
    try:
        activity = Activity.objects.filter(id=int(para.activity_id)).first()
        if not activity:
            raise BusinessException(ERR_ACTIVITY_NOT_EXIST)
        user, role = get_user(activity, request.user)
        if not user:
            raise BusinessException(ERR_USER_AUTH)
        result = activity_s.list_activity_expert(request.user, activity, user, para.keyword, para.rows, para.page)
    except Exception as ex:
        logger.exception(ex)
        return response_exception(ex)
    return response200(dict(c=SUCCESS[0], m=SUCCESS[1], d=result))


@check("POST", para=(
    {'name': 'activity_id'},
    {'name': 'keyword', 'default': ''},
    {'name': 'rows', 'default': 10},
    {'name': 'page', 'default': 1},
))
def api_available_add_activity_expert(request, para):
    try:
        activity = Activity.objects.filter(id=int(para.activity_id)).first()
        if not activity:
            raise BusinessException(ERR_ACTIVITY_NOT_EXIST)
        user, role = get_user(activity, request.user)
        if not user:
            raise BusinessException(ERR_USER_AUTH)
        result = activity_s.available_add_activity_expert(request.user, activity, user, para.keyword, para.rows, para.page)
    except Exception as ex:
        logger.exception(ex)
        return response_exception(ex)
    return response200(result)


@check("POST", para=(
    {'name': 'activity_id'},
    {'name': 'expert_id_list', 'default': ''},
))
def api_delete_activity_expert(request, para):
    try:
        activity = Activity.objects.get(pk=int(para.activity_id))
        if not activity:
            raise BusinessException(ERR_ACTIVITY_NOT_EXIST)
        user, role = get_user(activity, request.user)
        if not user:
            raise BusinessException(ERR_USER_AUTH)
        result = activity_s.remove_activity_expert(request.user, activity, user, [int(e) for e in para.expert_id_list.strip().strip(',').split(',')])
    except Exception as ex:
        logger.exception(ex)
        return response_exception(ex, ex.message)
    log_response(request, result)
    return response200(result)


@check("POST", para=(
    {'name': 'activity_id'},
    {'name': 'expert_id_list', 'default': ''},
))
def api_export_activity_expert(request, para):
    try:
        activity = Activity.objects.filter(id=int(para.activity_id)).first()
        if not activity:
            raise BusinessException(ERR_ACTIVITY_NOT_EXIST)
        user, role = get_user(activity, request.user)
        if not user:
            raise BusinessException(ERR_USER_AUTH)
        expert_id_list = [int(r) for r in para.expert_id_list.strip().strip(',').split(',')]
        expert_list = Expert.objects.filter(del_flag=FALSE_INT, id__in=expert_id_list)
        wb = activity_s.export_activity_expert(request.user, activity, user, role, expert_list)

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
    {'name': 'activity_id'},
))
def api_download_expert_template(request, para):
    try:
        activity = Activity.objects.filter(id=int(para.activity_id)).first()
        if not activity:
            raise BusinessException(ERR_ACTIVITY_NOT_EXIST)
        user, role = get_user(activity, request.user)
        if not user:
            raise BusinessException(ERR_USER_AUTH)
        wb = activity_s.download_expert_template(request.user, activity, user, role)
        fname = u'%s.xlsx' % suuid()
        response = HttpResponse(content_type='application/vnd.ms-excel')
        response['Content-Disposition'] = 'attachment; filename=' + fname.encode('utf-8')
        wb.save(response)
        return response

        path = os.path.join(settings.BASE_DIR, 'media/%s.xlsx' % suuid())
        wb.save(path)
        return response200({'c': SUCCESS[0], 'm': SUCCESS[1], 'd': path})
    except Exception as ex:
        logger.exception(ex)
        return response_exception(ex)


# 修改活动中的专家信息直接调用专家模块的接口


@check('POST', para=(
    {'name': 'from_activity_id', 'default': None},
    {'name': 'name', 'default': None},
))
def api_add_template(request, para):
    try:
        result = activity_s.add_template(request.user, para.from_activity_id, para.name)
    except Exception as ex:
        logger.exception(ex)
        return response_exception(ex, ex.message)
    return response200(result)


@check("POST")
def api_list_template(request):
    try:
        result = activity_s.list_template(request.user)
    except Exception as ex:
        logger.exception(ex)
        return response_exception(ex, ex.message)
    return response200(result)


@check("POST", para=(
    {'name': 'template_id'},
))
def api_delete_template(request, para):
    try:
        tplt = Activity.objects.filter(id=int(para.template_id), template_flag=FLAG_YES).first()
        if not tplt:
            raise BusinessException(ERR_TEMPLATE_NOT_EXIST)
        result = activity_s.del_activity(tplt)
    except Exception as ex:
        logger.exception(ex)
        return response_exception(ex, ex.message)
    return response200(result)


@check("POST", para=(
    {'name': 'area_id'},
    {'name': 'template_id'},
))
def api_add_activity(request, para):
    try:
        area = Area.objects.filter(del_flag=FLAG_NO, id=int(para.area_id)).first()
        tplt = Activity.objects.filter(id=int(para.template_id), template_flag=FLAG_YES).first()
        result = activity_s.add_activity(request.user, area, tplt)
    except Exception as ex:
        logger.exception(ex)
        return response_exception(ex)
    return response200(result)


@check("POST", para=(
    {'name': 'activity_id'},
    {'name': 'file', 'is_file': True, },
))
def api_import_winner(request, para):
    try:
        result = activity_s.import_winner(request.user, para.activity_id, para.file)
    except Exception as ex:
        logger.exception(ex)
        return response_exception(ex, ex.message)
    log_response(request, result)
    return response200(result)


@check("GET", auth=False, para=(
    {'name': 'activity_id'},
    {'name': 'rows', 'default': None},
    {'name': 'page', 'default': None},
    {'name': 'last_id', 'default': None},
))
def api_list_winner(request, para):
    try:
        result = activity_s.list_winner(request.user, para.activity_id, para.rows, para.page, para.last_id)
    except Exception as ex:
        logger.exception(ex)
        return response_exception(ex, ex.message)
    log_response(request, result)
    return response200(result)


@check("GET", auth=False, para=(
    {'name': 'activity_id'},
    {'name': 'tag'},
))
def api_tag_alias(request, para):
    try:
        activity = Activity.objects.get(pk=int(para.activity_id))
        if not activity:
            raise BusinessException(ERR_ACTIVITY_NOT_EXIST)
        result = activity_s.tag_alias(request.user, activity, para.tag)
    except Exception as ex:
        logger.exception(ex)
        return response_exception(ex, ex.message)
    return response200(dict(c=SUCCESS[0], m=SUCCESS[1], d=result))

