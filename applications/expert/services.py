#!/usr/bin/env python
# coding=utf-8
import logging

from django.conf import settings
import re
import json

from django.db.models import Q

from applications.activity.models import ExpertActivity
from applications.activity.share import expert
from applications.common.services import update_area_fullname, area_bind_region
from utils.const_def import *
from utils.const_err import *
from utils.file_fun import get_image_url
from applications.user.models import *
from applications.expert.models import Expert
from utils.utils_except import BusinessException


logger = logging.getLogger(__name__)


def list_expert_user(user, cur_user_id, name, area_id, manage_direct, is_show_store=None):
    name = name.strip() if name else ""
    expert_list = Expert.objects.filter(del_flag=FLAG_NO)
    if is_show_store:
        expert_list = expert_list.filter(is_show_store=is_show_store)
    else:
        expert_list = expert_list.filter(is_show_store=1)
    if name:
        # expert_list = expert_list.filter(name__contains=name)
        expert_list = expert_list.filter(Q(name__contains=name) | Q(account__mobile__contains=name) | Q(account__username__contains=name))

    if area_id:
        expert_list = expert_list.filter(area_id=area_id)
    if manage_direct:
        expert_list = expert_list.filter(area__manage_direct=FLAG_YES)

    expert_infos = expert_list.values("id", "account_id", "area_id", "account__username", "name", "sex",
                                      "area__area_name", "area__area_level", "area__area_code", 'institution',
                                      'is_show_homepage', "account__image__url", "area__manage_direct", "is_show_store",
                                      'position').order_by("-update_time")
    expert_infos = list(expert_infos)
    data = []
    for item in expert_infos:
        area_name = item["area__area_name"]
        if item["area__manage_direct"]:
            if item["area__area_level"] == LEVEL_PROVINCE:
                area_name = u"省直属"
            elif item["area__area_level"] == LEVEL_CITY:
                area_name = u"市直属"
            elif item["area__area_level"] == LEVEL_NATION:
                area_name = u"国直属"
            else:
                pass
        dict_tmp = {"id": item["id"], "name": item['name'], "sex": item['sex'], "username": item['account__username'],
                    'account_id': item['account_id'], "area_name": area_name, "area_id": item["area_id"],
                    "area_level": item['area__area_level'], "area_code": item["area__area_code"],
                    "institution": item['institution'], "is_show_homepage": item['is_show_homepage'],
                    "image_url": get_image_url(item["account__image__url"]) if item['account__image__url'] else "",
                    "is_show_store": item['is_show_store'],
                    "position": item['position'],
                    }
        data.append(dict_tmp)
    return dict(c=SUCCESS[0], m=SUCCESS[1], d=data)


def __check_username_valid(username):
    username = username.strip()
    if re.match('[gl]', username, re.I) and not re.search(r'\W', username) and len(username) > 12 and len(username) < 21:
        return {"c": SUCCESS[0], "m": SUCCESS[1], "d": []}
    else:
        if len(username) != 11 or not username.isdigit():
            return {"c": ERR_USER_USERNAME_ERROR[0], "m": ERR_USER_USERNAME_ERROR[1], "d": []}
    return {"c": SUCCESS[0], "m": SUCCESS[1], "d": []}


def add_expert_user(user, username, name, sex, institution, image_id, position, introduction,
                    area_id, direct_area_id):
    result = dict()

    # 注意institution机构名称、direct_area_id直属地区id，比如湖北省直属则需要direct_area_id传入湖北省id、area_id非直属并非机构传此参数三者传值方式
    # 1、添加各级直属机构专家/用户，需要传入direct_area_id、institution
    # 2、添加省、市、区县专家/用户，只需要传area_id
    # 3、添加区县下机构的专家/用户，可以只传入direct_area_id、institution,也可只传入area_id
    # 4、添加机构下的普通用户，需要传入direct_area_id，
    if direct_area_id and int(direct_area_id):
        direct_area = Area.objects.get(id=direct_area_id, del_flag=FALSE_INT)
        if direct_area.area_level == LEVEL_INSTITUTION or direct_area.manage_direct == TRUE_INT:
            # 机构添加普通用户/专家
            area_zone, _ = Area.objects.get_or_create(del_flag=FLAG_NO, area_name=USER_TYPE_NORMAL, parent_id=direct_area.id,
                                                      manage_direct=FLAG_NO, area_level=LEVEL_NONE)
        elif direct_area.area_level == LEVEL_COUNTY:
            # 添加区县下的机构用户/专家
            area_zone, _ = Area.objects.get_or_create(del_flag=FLAG_NO, area_name=institution, parent_id=direct_area.id,
                                                      manage_direct=FLAG_NO, area_level=direct_area.area_level >> 1)
            area_bind_region(area_zone)
        else:
            # 地区加直属机构用户/专家
            area_zone, _ = Area.objects.get_or_create(del_flag=FLAG_NO, area_name=institution, parent_id=direct_area.id,
                                                      manage_direct=FLAG_YES, area_level=direct_area.area_level >> 1)
            area_bind_region(area_zone)
    elif area_id and int(area_id):
        cur_area = Area.objects.get(id=area_id, del_flag=FALSE_INT)
        if cur_area.area_level >= LEVEL_INSTITUTION:
            area_zone = cur_area
        else:
            raise BusinessException(ERR_EXPERT_AREA)
    else:
        raise BusinessException(ERR_REQUEST_PARAMETER_ERROR)

    if not area_zone:
        return dict(c=REQUEST_PARAM_ERROR[0], m=REQUEST_PARAM_ERROR[1])

    update_area_fullname(area_zone.id)

    # 检查用户名格式是否正确
    resp_code = __check_username_valid(username)
    if resp_code['c'] != SUCCESS[0]:
        return resp_code
    account = Account.objects.filter(del_flag=FLAG_NO, username=username).first()
    if not account:
        account = Account.objects.create_user(username, password=settings.DEFAULT_PASSWORD)
        account.name = name if name else ""
        if sex:  account.sex = sex
        if re.match('[gl]', username, re.I):
            account.code = username
        elif len(username) == 11 and username.isdigit():
            account.mobile = username
        if image_id:
            account.image_id = int(image_id)
        account.save()
        expertadd = Expert.objects.create(account=account, name=name, sex=sex, area=area_zone, institution=institution,
                                          position=position, introduction=introduction, is_show_store=1)
    else:
        expertadd = Expert.objects.filter(del_flag=FLAG_NO, account=account).first()
        if expertadd:
            logger.info(u"该用户已经创建过专家")
            expertadd.is_show_store = 1
            expertadd.save()
        else:
            expertadd = Expert.objects.create(account=account, name=name, sex=sex, area=area_zone, institution=institution,
                                              position=position, introduction=introduction)

        # 如果用户尚未确认资料，则以新资料为准。
        if not account.is_data_confirm:
            account.name = name
            account.sex = sex
            account.save()

            expertadd.name = name
            expertadd.sex = sex
            expertadd.area = area_zone
            expertadd.institution = institution
            expertadd.position = position
            expertadd.introduction = introduction
            expertadd.save()

    result['expert_id'] = expertadd.id
    return dict(c=SUCCESS[0], m=SUCCESS[1], d=result)


def mod_expert_user(user, expert_id, username, name, sex, institution,
                    image_id, position, introduction, area_id, direct_area_id):
    result = dict()
    # 检查用户是否存在，检查传入的当前用户是否是登陆的用户
    # cur_user = User.objects.filter(del_flag=FLAG_NO, id=cur_user_id).first()
    # if not cur_user:
    #     raise BusinessException(ERR_REQUEST_PARAMETER_ERROR)
    # if cur_user.account != user:
    #     raise BusinessException(ERR_USER_AUTH)

    # 检查expert是否存在
    expert = Expert.objects.filter(id=expert_id, del_flag=FALSE_INT).first()
    if not expert:
        raise BusinessException(ERR_EXPERT_NOT_EXIST)

    if expert.account.is_data_confirm:
        raise BusinessException(ERR_ACCOUNTDATA_IS_CONFIRM)

    # 注意institution机构名称、direct_area_id直属地区id，比如湖北省直属则需要direct_area_id传入湖北省id、area_id非直属并非机构传此参数三者传值方式
    # 1、添加各级直属机构专家/用户，需要传入direct_area_id、institution
    # 2、添加省、市、区县专家/用户，只需要传area_id
    # 3、添加区县下机构的专家/用户，可以只传入direct_area_id、institution,也可只传入area_id
    # 4、添加机构下的普通用户，需要传入direct_area_id，
    if direct_area_id and int(direct_area_id):
        direct_area = Area.objects.get(id=direct_area_id, del_flag=FALSE_INT)
        if direct_area.area_level == LEVEL_INSTITUTION or direct_area.manage_direct == TRUE_INT:
            # 机构添加普通用户/专家
            area_zone, _ = Area.objects.get_or_create(del_flag=FLAG_NO, area_name=USER_TYPE_NORMAL, parent_id=direct_area.id,
                                                      manage_direct=FLAG_NO, area_level=LEVEL_NONE)
        elif direct_area.area_level == LEVEL_COUNTY:
            # 添加区县下的机构用户/专家
            area_zone, _ = Area.objects.get_or_create(del_flag=FLAG_NO, area_name=institution, parent_id=direct_area.id,
                                                      manage_direct=FLAG_NO, area_level=direct_area.area_level >> 1)
            area_bind_region(area_zone)
        else:
            # 地区加直属机构用户/专家
            area_zone, _ = Area.objects.get_or_create(del_flag=FLAG_NO, area_name=institution, parent_id=direct_area.id,
                                                      manage_direct=FLAG_YES, area_level=direct_area.area_level >> 1)
            area_bind_region(area_zone)
    elif area_id and int(area_id):
        cur_area = Area.objects.get(id=area_id, del_flag=FALSE_INT)
        if cur_area.area_level >= LEVEL_INSTITUTION:
            area_zone = cur_area
        else:
            raise BusinessException(ERR_EXPERT_AREA)
    else:
        raise BusinessException(ERR_REQUEST_PARAMETER_ERROR)

    if not area_zone:
        raise BusinessException(REQUEST_PARAM_ERROR)

    update_area_fullname(area_zone.id)

    # 检查用户名格式是否正确
    resp_code = __check_username_valid(username)
    if resp_code['c'] != SUCCESS[0]:
        return resp_code

    # 检查除了自己，其它人是否使用了此用户名。
    account = Account.objects.filter(del_flag=FLAG_NO, username=username).exclude(id=expert.account_id).first()
    if not account:
        account = Account.objects.get(id=expert.account_id)
        account.name = name if name else ""
        if sex:  account.sex = sex
        if re.match('[gl]', username, re.I):
            account.code = username
        elif len(username) == 11 and username.isdigit():
            account.mobile = username
        if image_id:
            account.image_id = int(image_id)
        account.save()

        expert.account = account
        expert.name = name
        expert.sex = sex
        expert.area = area_zone
        expert.institution = institution
        expert.position = position
        expert.introduction = introduction
        expert.save()

        result['expert_id'] = expert_id
        return dict(c=SUCCESS[0], m=SUCCESS[1], d=result)
    else:
        raise BusinessException(ERR_USERNAME_DUPLICATE)


def delete_expert_user(user, cur_user_id, expert_id_list, name, area_id, manage_direct, del_all_expert):
    cur_user = User.objects.filter(del_flag=FLAG_NO, id=cur_user_id).first()
    if cur_user.account != user:
        return dict(c=ERR_USER_AUTH[0], m=ERR_USER_AUTH[1])

    if expert_id_list:
        expert_id_list = map(lambda x: int(x), json.loads(expert_id_list))
    elif del_all_expert:
        del_expertdata_list = list_expert_user(user, cur_user_id, name, area_id, manage_direct)['d']
        expert_id_list = list()
        for each_expertdata in del_expertdata_list:
            expert_id_list.append(each_expertdata['id'])
    else:
        # expert_id_list 和del_all_expert不能同时为空
        raise BusinessException(REQUEST_PARAM_ERROR)

    # # 检查专家是不是在活动中
    # expertactivitys = ExpertActivity.objects.filter(expert_id__in=expert_id_list, del_flag=FALSE_INT)
    # if expertactivitys:
    #     raise BusinessException(ERR_CANT_DEL_EXPERT_INACTIVITY)
    #
    # del_id_enable = Expert.objects.filter(del_flag=FLAG_NO, area__parent=cur_user.area, id__in=expert_id_list).\
    #     values_list("id", flat=True)
    # del_id_enable = list(del_id_enable)
    # del_id_disable = list(set(expert_id_list) - set(del_id_enable))
    # Expert.objects.filter(del_flag=FLAG_NO, id__in=del_id_enable).update(del_flag=FLAG_YES)
    # if del_id_disable:
    #     if del_id_enable:
    #         msg = u"user_id_list {0} deleted. while user_id_list {1} can not delete ".\
    #             format(del_id_enable, del_id_disable)
    #         return dict(c=ERR_PARTLY_DELETE_SUCCESS[0], m=ERR_PARTLY_DELETE_SUCCESS[1], d=[msg])
    #     else:
    #         return dict(c=ERR_REQUEST_PARAMETER_ERROR[0], m=ERR_REQUEST_PARAMETER_ERROR[1])
    # else:
    #     return dict(c=SUCCESS[0], m=SUCCESS[1], d=[])

    # V3版本删除专家仅修改专家显示状态
    result = Expert.objects.filter(del_flag=FLAG_NO, area__parent=cur_user.area, id__in=expert_id_list).update(is_show_store=0)
    return dict(c=SUCCESS[0], m=SUCCESS[1], d=result)


def detail_expert(user, expert_id):
    e = Expert.objects.filter(del_flag=FLAG_NO, id=expert_id).first()
    if not e:
        return dict(c=ERR_REQUEST_PARAMETER_ERROR[0], m=ERR_REQUEST_PARAMETER_ERROR[1])
    return dict(c=SUCCESS[0], m=SUCCESS[1], d=expert(e))


def display_expert(user, area_id):
    area = Area.objects.filter(del_flag=FLAG_NO, id=area_id).first()
    if not area:
        return dict(c=ERR_REQUEST_PARAMETER_ERROR[0], m=ERR_REQUEST_PARAMETER_ERROR[1])
    expert_infos = Expert.objects.filter(del_flag=FLAG_NO, area=area, is_show_homepage=FLAG_YES).\
        values("id", "account_id", "area_id", "account__username", "name", "sex", "area__area_name",
               "area__area_level", "area__area_code", 'institution', 'is_show_homepage', "account__image__url")
    expert_infos = list(expert_infos)
    data = []
    for item in expert_infos:
        dict_tmp = {"id": item["id"], "name": item['name'], "sex": item['sex'], "username": item['account__username'],
                    'account_id': item['account_id'], "area_name": item['area__area_name'], "area_id": item["area_id"],
                    "area_level": item['area__area_level'], "area_code": item["area__area_code"],
                    "institution": item['institution'], "is_show_homepage": item['is_show_homepage'],
                    "image_url": get_image_url(item["account__image__url"]) if item['account__image__url'] else ""
                    }
        data.append(dict_tmp)
    return dict(c=SUCCESS[0], m=SUCCESS[1], d=data)


