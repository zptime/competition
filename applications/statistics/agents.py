#!/usr/bin/python
# -*- coding=utf-8 -*-
from applications.activity.models import Ranks, Role
from applications.common.services import get_sub_area_id_list
from applications.user.models import *
from utils.const_err import *
from utils.file_fun import *
from applications.work.models import *
from applications.statistics.models import *
from django.db.models import Q
from django.db.models import Count
from django.db.models import Sum
from django.db import transaction

import traceback
import json

from utils.utils_except import BusinessException


def list_total_statistics(user, activity_id=""):
    if not activity_id:
        logger.error("parameters incomplete")
        return {"c": ERR_REQUESTWAY[0], "m": ERR_REQUESTWAY[1], "d": []}

    activity_id = int(activity_id)
    total_statistics_list = []

    cur_activity = Activity.objects.filter(id=activity_id, del_flag=FALSE_INT).first()
    if not cur_activity:
        raise BusinessException(ERR_ACTIVITY_ID_ERROR)

    cur_activity_area_level = cur_activity.user.area.area_level

    if cur_activity_area_level == LEVEL_PROVINCE:
        manage_direct_name = u'省直属'
    elif cur_activity_area_level == LEVEL_CITY:
        manage_direct_name = u'市直属'
    else:
        manage_direct_name = ''

    # 只查询市级的统计信息
    # area_statistics_list = []
    # area_worknumber_info_list = AreaWorkNumber.objects.filter(activity_id=activity_id, del_flag=0, area__area_level=LEVEL_CITY)\
    #     .order_by('-work_number').values("area__area_name", "work_number")
    # if area_worknumber_info_list:
    #     for area_worknumber_info in area_worknumber_info_list:
    #         area_statistics = dict(category=area_worknumber_info['area__area_name'],
    #                                work_number=str(area_worknumber_info['work_number'])
    #                                )
    #         area_statistics_list.append(area_statistics)
    # total_statistics_list.append(dict(data=area_statistics_list))

    # 修改一下，需要查询地市下所有地区的合计，而不是只查地市自己提交的数据
    area_statistics_list = []
    # 先查省直属/市直属
    if cur_activity_area_level in (LEVEL_PROVINCE, LEVEL_CITY):
        area_direct_worknumber_info_list = AreaWorkNumber.objects.filter(activity_id=activity_id, del_flag=0,
                                                                         area__parent__area_level=cur_activity_area_level,
                                                                         area__manage_direct=TRUE_INT) \
            .aggregate(sum=Sum('work_number'))
        area_statistics = dict(category=manage_direct_name,
                               work_number=area_direct_worknumber_info_list['sum'] if area_direct_worknumber_info_list['sum'] else 0
                               )
        area_statistics_list.append(area_statistics)

    # 再查活动直接下级的数据
    child_areas = Area.objects.filter(parent_id=cur_activity.user.area_id, del_flag=FALSE_INT, manage_direct=FALSE_INT)
    for each_child_area in child_areas:
        sub_area_list = get_sub_area_id_list(each_child_area.id)
        sub_area_list.append(each_child_area.id)

        area_worknumber_info_list = AreaWorkNumber.objects.filter(activity_id=activity_id, del_flag=FALSE_INT,
                                                                  area_id__in=sub_area_list) \
            .aggregate(sum=Sum('work_number'))
        area_statistics = dict(category=each_child_area.area_name,
                               work_number=area_worknumber_info_list['sum'] if area_worknumber_info_list['sum'] else 0
                               )
        area_statistics_list.append(area_statistics)
    # 按数量从小到大进行排序
    area_statistics_list = sorted(area_statistics_list, key=lambda e: e.__getitem__('work_number'))
    # 按从大到小排序
    area_statistics_list = area_statistics_list[::-1]
    total_statistics_list.append(dict(data=area_statistics_list))

    # 按获奖等级统计
    level_statistics_list = []
    level_worknumber_info_list = LevelWorkNumber.objects.filter(activity_id=activity_id, del_flag=FALSE_INT, rank__del_flag=FALSE_INT).values("rank", "rank__name") \
        .annotate(sum_worknumber=Sum("work_number")).values("rank", "rank__name", "sum_worknumber")
    if level_worknumber_info_list:
        for level_worknumber_info in level_worknumber_info_list:
            level_statistics = dict(category=level_worknumber_info['rank__name'],
                                    work_number=str(level_worknumber_info['sum_worknumber'])
                                    )
            level_statistics_list.append(level_statistics)
    total_statistics_list.append(dict(data=level_statistics_list))

    phase_statistics_list = []
    phase_worknumber_info_list = PhaseWorkNumber.objects.filter(activity_id=activity_id, del_flag=FALSE_INT).values("phase", "work_number")
    if phase_worknumber_info_list:
        for phase_worknumber_info in phase_worknumber_info_list:
            phase_statistics = dict(category=phase_worknumber_info['phase'],
                                    work_number=str(phase_worknumber_info['work_number'])
                                    )
            phase_statistics_list.append(phase_statistics)
    total_statistics_list.append(dict(data=phase_statistics_list))

    project_statistics_list = []
    project_worknumber_info_list = ProjectWorkNumber.objects.filter(activity_id=activity_id, del_flag=FALSE_INT).values("project", "work_number")
    if project_worknumber_info_list:
        for project_worknumber_info in project_worknumber_info_list:
            project_statistics = dict(category=project_worknumber_info['project'],
                                      work_number=str(project_worknumber_info['work_number'])
                                      )
            project_statistics_list.append(project_statistics)
    total_statistics_list.append(dict(data=project_statistics_list))

    subject_statistics_list = []
    subject_worknumber_info_list = SubjectWorkNumber.objects.filter(activity_id=activity_id, del_flag=FALSE_INT).values("subject", "work_number")
    if subject_worknumber_info_list:
        for subject_worknumber_info in subject_worknumber_info_list:
            subject_statistics = dict(category=subject_worknumber_info['subject'],
                                      work_number=str(subject_worknumber_info['work_number'])
                                      )
            subject_statistics_list.append(subject_statistics)

    # 由于用户导入作品时，填入的学科很多是按自己的意思随意填写，导致统计页面数据较零散，此处做个汇总归类
    # 先查询配置了哪些学科
    subjects = WorkAttr.objects.filter(activity_id=activity_id, del_flag=FALSE_INT, name=u'所属学科').first()
    if not subjects:
        subject_group_sum_list = subject_statistics_list
    else:
        subject_group_sum_list = list()
        subject_group_sum_dict = dict()
        subjects = subjects.values.split(';')
        # 先将所有配置的科目数量置为0
        for each_subject in subjects:
            subject_group_sum_dict[each_subject] = 0
        subject_group_sum_dict[u'其它'] = 0

        # 再将查询的数据进行分别填入配置的类型，如果滑配置，则放入其它中
        for each_subject_statistics in subject_statistics_list:
            if each_subject_statistics['category'] in subject_group_sum_dict:
                subject_group_sum_dict[each_subject_statistics['category']] = subject_group_sum_dict[each_subject_statistics['category']] + int(each_subject_statistics['work_number'])
            else:
                subject_group_sum_dict[u'其它'] = subject_group_sum_dict[u'其它'] + int(each_subject_statistics['work_number'])

        # 将字典转list
        for k, v in subject_group_sum_dict.items():
            tmpdict = {
                "category": k,
                "work_number": v,
            }
            subject_group_sum_list.append(tmpdict)

    total_statistics_list.append(dict(data=subject_group_sum_list))

    dict_resp = {"c": SUCCESS[0], "m": SUCCESS[1], "d": total_statistics_list}
    return dict_resp


def list_country_statistics(user, activity_id=""):
    if not activity_id:
        logger.error("parameters incomplete")
        return {"c": ERR_REQUESTWAY[0], "m": ERR_REQUESTWAY[1], "d": []}

    activity_id = int(activity_id)

    country_statistics_list = []
    country_worknumber_info_list = AreaWorkNumber.objects.filter(activity_id=activity_id, del_flag=0, area__area_level=LEVEL_COUNTY).values("area__area_name", "work_number")
    if country_worknumber_info_list:
        for country_worknumber_info in country_worknumber_info_list:
            country_statistics = dict(category=country_worknumber_info['area__area_name'],
                                      work_number=str(country_worknumber_info['work_number'])
                                      )
            country_statistics_list.append(country_statistics)

    dict_resp = {"c": SUCCESS[0], "m": SUCCESS[1], "d": [dict(data=country_statistics_list)]}
    return dict_resp


def list_level_statistics(user, activity_id="", area_id="", direct_level=""):
    activity_id = int(activity_id)

    level_statistics_list = []

    level_worknumber_info_list = LevelWorkNumber.objects.filter(activity_id=activity_id, del_flag=0)
    if area_id:
        level_worknumber_info_list.filter(area_id=area_id)

    # 查询省市直属功能。
    if direct_level:
        level_worknumber_info_list.filter(area__area_level=direct_level, area__manage_direct=TRUE_INT)

    level_worknumber_info_list = level_worknumber_info_list.values("rank_id", "rank__name") \
        .annotate(sum_worknumber=Sum("work_number")).values("rank_id", "rank__name", "sum_worknumber")

    # if area_id:
    #     level_worknumber_info_list = LevelWorkNumber.objects.filter(activity_id=activity_id, area_id=area_id, del_flag=0).values("rank_id", "rank__name") \
    #         .annotate(sum_worknumber=Sum("work_number")).values("rank_id", "rank__name", "sum_worknumber")
    # else:
    #
    #     level_worknumber_info_list = LevelWorkNumber.objects.filter(activity_id=activity_id, del_flag=0).values("rank_id", "rank__name") \
    #         .annotate(sum_worknumber=Sum("work_number")).values("rank_id", "rank__name", "sum_worknumber")

    if level_worknumber_info_list:
        for level_worknumber_info in level_worknumber_info_list:
            level_statistics = dict(category=level_worknumber_info['rank__name'],
                                    work_number=str(level_worknumber_info['sum_worknumber'])
                                    )
            level_statistics_list.append(level_statistics)

    dict_resp = {"c": SUCCESS[0], "m": SUCCESS[1], "d": [dict(data=level_statistics_list)]}
    return dict_resp


@transaction.atomic
def statistics_number_update():
    # 得到所有需要更新作品数量的活动
    activity_info_list = Activity.objects.filter(~Q(stage=1), del_flag=0).values("id")
    if not activity_info_list:
        return u"没有需要更新的统计数据"

    try:
        for activity_info in activity_info_list:
            activity_id = activity_info["id"]
            # activity_type_id = activity_info["activity_type_id"]
            # level_range = activity_info["level_range"]
            # advanced_level_required = activity_info["advanced_level_required"]

            ranks = Ranks.objects.filter(activity_id=activity_id, del_flag=FALSE_INT).values_list("id", flat=True)

            # 如果数据库中没有关于城市作品数量的统计，则创建该统计
            if not AreaWorkNumber.objects.filter(activity_id=activity_id, del_flag=0).exists():
                for each_areaid in get_total_areaid_list():
                    AreaWorkNumber.objects.create(activity_id=activity_id, area_id=each_areaid, work_number=0)
            else:
                # 先将所有数据重置为0，后面逻辑中重新统计，解决有人上传作品后删除，当统计项目作品数量为0无法统计的情况。
                AreaWorkNumber.objects.filter(activity_id=activity_id, del_flag=0).update(work_number=0)
                LevelWorkNumber.objects.filter(activity_id=activity_id, del_flag=0).update(work_number=0)
                SubjectWorkNumber.objects.filter(activity_id=activity_id, del_flag=0).update(work_number=0)
                PhaseWorkNumber.objects.filter(activity_id=activity_id, del_flag=0).update(work_number=0)
                ProjectWorkNumber.objects.filter(activity_id=activity_id, del_flag=0).update(work_number=0)

            # 如果数据库中没有关于等级作品数量的统计，则创建该统计
            if not LevelWorkNumber.objects.filter(activity_id=activity_id, del_flag=FALSE_INT, rank__del_flag=FALSE_INT).exists():
                # 如果存在作品等级
                if ranks:
                    # level_range = json.loads(level_range)
                    # if advanced_level_required == 1:
                    #     level_range.append(u'特等奖')
                    for each_cityid in get_city_areaid_list():
                        for each_rankid in get_activity_rankid_list(activity_id):
                            LevelWorkNumber.objects.create(activity_id=activity_id, area_id=each_cityid, rank_id=each_rankid, work_number=0)

            # 更新区域作品数量表
            area_worknumber_info_list = Work.objects.filter(Q(activity_id=activity_id), status__gt=5, del_flag=0).values("area_id") \
                .annotate(work_number=Count('id')).values("area_id", "work_number")
            if area_worknumber_info_list:
                for area_worknumber_info in area_worknumber_info_list:
                    if not AreaWorkNumber.objects.filter(activity_id=activity_id, area_id=area_worknumber_info["area_id"], del_flag=0).exists():
                        AreaWorkNumber.objects.create(activity_id=activity_id, area_id=area_worknumber_info["area_id"],
                                                      work_number=area_worknumber_info["work_number"])
                    else:
                        AreaWorkNumber.objects.filter(activity_id=activity_id, area_id=area_worknumber_info["area_id"], del_flag=0) \
                            .update(work_number=area_worknumber_info["work_number"])

            # 更新等级作品数量表
            level_worknumber_info_list = Work.objects.filter(Q(activity_id=activity_id),
                                                             Q(finalscore__rank__isnull=False), Q(status=8), del_flag=0) \
                .values("area_id", "finalscore__rank_id").annotate(work_number=Count('id')).values("area_id", "finalscore__rank_id", "work_number")
            if level_worknumber_info_list:
                for level_worknumber_info in level_worknumber_info_list:
                    if not LevelWorkNumber.objects.filter(activity_id=activity_id, area_id=level_worknumber_info["area_id"],
                                                          rank_id=level_worknumber_info["finalscore__rank_id"], del_flag=0).exists():
                        LevelWorkNumber.objects.create(activity_id=activity_id, area_id=level_worknumber_info["area_id"],
                                                       rank_id=level_worknumber_info["finalscore__rank_id"],
                                                       work_number=level_worknumber_info["work_number"])
                    else:
                        LevelWorkNumber.objects.filter(activity_id=activity_id, area_id=level_worknumber_info["area_id"],
                                                       rank_id=level_worknumber_info["finalscore__rank_id"], del_flag=0) \
                            .update(work_number=level_worknumber_info["work_number"])

            # 更新学科作品数量表
            subject_worknumber_info_list = Work.objects.filter(Q(activity_id=activity_id), ~Q(subject=""), status__gt=5, del_flag=0).values("subject") \
                .annotate(work_number=Count(id)).values("subject", "work_number")
            if subject_worknumber_info_list:
                for subject_worknumber_info in subject_worknumber_info_list:
                    if not SubjectWorkNumber.objects.filter(activity_id=activity_id, subject=subject_worknumber_info["subject"], del_flag=0).exists():
                        SubjectWorkNumber.objects.create(activity_id=activity_id, subject=subject_worknumber_info["subject"],
                                                         work_number=subject_worknumber_info["work_number"])
                    else:
                        SubjectWorkNumber.objects.filter(activity_id=activity_id, subject=subject_worknumber_info["subject"], del_flag=0) \
                            .update(work_number=subject_worknumber_info["work_number"])

            # 更新学段作品数量表
            phase_worknumber_info_list = Work.objects.filter(Q(activity_id=activity_id), ~Q(phase=""), status__gt=5, del_flag=0).values("phase") \
                .annotate(work_number=Count(id)).values("phase", "work_number")
            if phase_worknumber_info_list:
                for phase_worknumber_info in phase_worknumber_info_list:
                    if not PhaseWorkNumber.objects.filter(activity_id=activity_id, phase=phase_worknumber_info["phase"], del_flag=0).exists():
                        PhaseWorkNumber.objects.create(activity_id=activity_id, phase=phase_worknumber_info["phase"],
                                                       work_number=phase_worknumber_info["work_number"])
                    else:
                        PhaseWorkNumber.objects.filter(activity_id=activity_id, phase=phase_worknumber_info["phase"], del_flag=0) \
                            .update(work_number=phase_worknumber_info["work_number"])

            # 更新项目作品数量表
            project_worknumber_info_list = Work.objects.filter(Q(activity_id=activity_id), ~Q(project=""), status__gt=5, del_flag=0).values("project") \
                .annotate(work_number=Count(id)).values("project", "work_number")
            if project_worknumber_info_list:
                for project_worknumber_info in project_worknumber_info_list:
                    if not ProjectWorkNumber.objects.filter(activity_id=activity_id, project=project_worknumber_info["project"], del_flag=0).exists():
                        ProjectWorkNumber.objects.create(activity_id=activity_id, project=project_worknumber_info["project"],
                                                         work_number=project_worknumber_info["work_number"])
                    else:
                        ProjectWorkNumber.objects.filter(activity_id=activity_id, project=project_worknumber_info["project"], del_flag=0) \
                            .update(work_number=project_worknumber_info["work_number"])

    except Exception:
        sErrInfo = traceback.format_exc()
        logger.error(sErrInfo)


def get_total_areaid_list():
    return Area.objects.filter(del_flag=FALSE_INT).values_list("id", flat=True)


def get_city_areaid_list():
    return Area.objects.filter(del_flag=FALSE_INT, area_level=LEVEL_CITY).values_list("id", flat=True)


def get_activity_rankid_list(activity_id):
    return Ranks.objects.filter(activity_id=activity_id, del_flag=FALSE_INT).order_by('sn').values_list("id", flat=True)


@transaction.atomic
def work_number_update():
    # 得到所有需要更新作品数量的活动
    # activity_info_list = Activity.objects.filter(~Q(stage=1), del_flag=0).values("id")
    activity_info_list = Activity.objects.filter(stage__in=[ACTIVITY_STAGE_UPLOAD, ACTIVITY_STAGE_GROUP, ACTIVITY_STAGE_REVIEW, ACTIVITY_STAGE_PUBLIC], del_flag=0).values("id")
    if not activity_info_list:
        return u"没有需要更新的作品数量统计"

    try:
        for activity_info in activity_info_list:
            activity_id = activity_info["id"]
            # activity_type_id = activity_info["activity_type_id"]

            # 查询该活动所有用户列表,从原统计表格中，删除不在用户列表中的统计记录
            activity_user_ids = Role.objects.filter(activity_id=activity_id, del_flag=FALSE_INT).values_list('user_id', flat=True).distinct()
            UserWorkNumber.objects.filter(activity_id=activity_id, del_flag=FALSE_INT).exclude(user_id__in=activity_user_ids).update(del_flag=TRUE_INT)

            # 统计所有该活动每个用户提交的作品数量，并更新到统计表中
            has_worknum_user_ids = []
            user_work_number_list = Work.objects.filter(activity_id=activity_id, status__gt=2, del_flag=0).values("uploader_id")\
                .annotate(uploader_id_num=Count("uploader_id")).values("uploader_id", "uploader_id_num")
            for each_user_work_number in user_work_number_list:
                UserWorkNumber.objects.update_or_create(activity_id=activity_id, user_id=each_user_work_number["uploader_id"],
                                                        del_flag=FALSE_INT,
                                                        defaults={'work_number': each_user_work_number["uploader_id_num"]},)
                # cur_user_id = get_userid_by_accountid(each_user_work_number['uploader_id'], activity_id)
                has_worknum_user_ids.append(each_user_work_number['uploader_id'])

            # 对于当前活动中，未提交过作品的用户，直接将上传作品数量置为0
            no_work_users = set(activity_user_ids) - set(has_worknum_user_ids)
            for each_no_work_user in no_work_users:
                UserWorkNumber.objects.update_or_create(activity_id=activity_id, user_id=each_no_work_user,
                                                        del_flag=FALSE_INT,
                                                        defaults={'work_number': 0},)

            # 统计用户审批数量及用户未审批数量
            activity_worknumbers = UserWorkNumber.objects.filter(activity_id=activity_id, del_flag=FALSE_INT)
            for each_role in activity_worknumbers:
                role_area_level = each_role.user.area.area_level
                # 只有市州、区县、学校用户需要审批其它人作品
                if role_area_level not in (LEVEL_CITY, LEVEL_COUNTY, LEVEL_INSTITUTION):
                    continue

                role_area_id = each_role.user.area_id
                sub_area_id_list = get_sub_area_id_list(role_area_id)
                sub_area_id_list.append(role_area_id)

                works = Work.objects.filter(activity_id=activity_id, del_flag=FALSE_INT, area_id__in=sub_area_id_list)
                if role_area_level == LEVEL_CITY:
                    approve_num = len(works.filter(status__gt=WORK_STATUS_CITY_EXAMINING[0]))
                    noprove_num = len(works.filter(status=WORK_STATUS_CITY_EXAMINING[0]))
                elif role_area_level == LEVEL_COUNTY:
                    approve_num = len(works.filter(status__gt=WORK_STATUS_COUNTRY_EXAMINING[0]))
                    noprove_num = len(works.filter(status=WORK_STATUS_COUNTRY_EXAMINING[0]))
                elif role_area_level == LEVEL_INSTITUTION:
                    approve_num = len(works.filter(status__gt=WORK_STATUS_SCHOOL_EXAMINING[0]))
                    noprove_num = len(works.filter(status=WORK_STATUS_SCHOOL_EXAMINING[0]))
                else:
                    # 前面已经限制，正常情况不会到这来，仅仅为了让编辑器不要提示我没定义变量。
                    approve_num = 0
                    noprove_num = 0

                each_role.approve_nubmer = approve_num
                each_role.noprove_nubmer = noprove_num
                each_role.save()

        return u"作品数量统计更新完成"

    except Exception:
        sErrInfo = traceback.format_exc()
        logger.error(sErrInfo)


def get_userid_by_accountid(account_id, activity_id):
    # 查询当前用户id
    role = Role.objects.filter(activity_id=activity_id, user__account_id=account_id, del_flag=FALSE_INT).first()
    if role:
        cur_user_id = role.user_id
    else:
        cur_user_id = ''
    return cur_user_id
