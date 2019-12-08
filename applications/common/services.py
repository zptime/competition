# -*- coding=utf-8 -*-

import logging
from django.core.cache import cache
from applications.activity.models import Role, ExpertActivity
from applications.user.models import LEVEL_INSTITUTION, LEVEL_COUNTY, LEVEL_CITY, LEVEL_PROVINCE, Area, User, LEVEL_NATION, LEVEL_NONE, Region
from utils.const_def import *
from utils.const_err import *
from utils.utils_bin import has_area
from utils.utils_except import BusinessException
from utils.utils_type import bool2str

logger = logging.getLogger(__name__)


def api_common_test(request, testparam1):
    logger.info(testparam1)
    if testparam1.lower() != 'ok':
        raise BusinessException(FAIL)
    result = testparam1
    return result


def get_account_activity_role(activity_id=0, account_id=0):
    # 检查用户是否有该活动权限，并获取用户当前类型
    result = set()

    # 检查是否为活动专家或用户
    expertactivity = ExpertActivity.objects.filter(activity_id=activity_id, expert__account_id=account_id, expert__del_flag=FALSE_INT)
    userroles = Role.objects.filter(activity_id=activity_id, user__account_id=account_id, del_flag=FALSE_INT)
    if not userroles and not expertactivity:
        raise BusinessException(ERR_USER_AUTH)

    # 专家
    if expertactivity:
        result.add(USER_TYPE_EXPERT)

    # 用户
    for each_user in userroles:
        if has_area(each_user.user.area.area_level, [LEVEL_NONE]):
            result.add(USER_TYPE_NORMAL)
        if has_area(each_user.user.area.area_level, [LEVEL_INSTITUTION]):
            result.add(USER_TYPE_INSTITUTION_ADMIN)
        if has_area(each_user.user.area.area_level, [LEVEL_COUNTY]):
            result.add(USER_TYPE_COUNTRY_ADMIN)
        if has_area(each_user.user.area.area_level, [LEVEL_CITY]):
            result.add(USER_TYPE_CITY_ADMIN)
        if has_area(each_user.user.area.area_level, [LEVEL_PROVINCE]):
            result.add(USER_TYPE_PROVINCE_ADMIN)
        if has_area(each_user.user.area.area_level, [LEVEL_NATION]):
            result.add(USER_TYPE_NATION_ADMIN)

        # 有权限的所有人都同时是普通用户，可以上传作品，可以修改自己上传未提交的作品。
        # 此处已修改，只有没有层级的人，都是普通用户。这些人目前应该都挂在机构下
        # result.add(USER_TYPE_NORMAL)

        # 检查用户是否整个活动最高管理员
        if not each_user.parent_role:
            result.add(USER_TYPE_ACTIVITY_ADMIN)

    return list(result)


def get_user_activity_role(activity_id=0, user_id=0):
    # 检查非专家用户是的用户类型
    result = set()

    # 检查是否为活动用户
    userroles = Role.objects.filter(activity_id=activity_id, user_id=user_id, del_flag=FALSE_INT)
    if not userroles:
        raise BusinessException(ERR_USER_AUTH)

    # 用户
    for each_user in userroles:
        if has_area(each_user.user.area.area_level, [LEVEL_INSTITUTION]):
            result.add(USER_TYPE_INSTITUTION_ADMIN)
        if has_area(each_user.user.area.area_level, [LEVEL_COUNTY]):
            result.add(USER_TYPE_COUNTRY_ADMIN)
        if has_area(each_user.user.area.area_level, [LEVEL_CITY]):
            result.add(USER_TYPE_CITY_ADMIN)
        if has_area(each_user.user.area.area_level, [LEVEL_PROVINCE]):
            result.add(USER_TYPE_PROVINCE_ADMIN)

        # 有权限的所有人都同时是普通用户，可以上传作品，可以修改自己上传未提交的作品。此处也可做预留普通用户的口子
        result.add(USER_TYPE_NORMAL)

        # 检查用户是否整个活动最高管理员
        if not each_user.parent_role:
            result.add(USER_TYPE_ACTIVITY_ADMIN)

    return list(result)


def get_sub_area_id_list(area_id):
    result = []
    return get_sub_area_id_list_recursion([area_id, ], result)


def get_sub_area_id_list_recursion(area_id_list, result):
    # 递归查询获取所有的子节点列表，不包含自已，返回扁平的list，非树形结构
    result_in_length = len(set(result))
    son_area = Area.objects.filter(parent_id__in=area_id_list, del_flag=FALSE_INT).values_list('id', flat=True)
    if not son_area:
        return list(set(result))
    else:
        result.extend(list(son_area))
        result = list(set(result))
        # 避免递归死循环处理
        result_out_length = len(result)
        if result_in_length == result_out_length:
            logger.error('请开发注意：查询id为%s时，发现area表有循环节点！' % str(area_id_list))
            return list(set(result))
        get_sub_area_id_list_recursion(son_area, result)
    return list(set(result))


def get_account_activity_area(activity_id, account_id, area_level):
    """
    查询用户在当前活动下对应的地区
    :param activity_id:
    :param account_id:
    :param area_level: LEVEL_PROVINCE 省，LEVEL_CITY 市， LEVEL_COUNTY 县，LEVEL_INSTITUTION 机构
    :return:
    """
    userid_list = Role.objects.filter(activity_id=activity_id, user__account_id=account_id, del_flag=FALSE_INT).values_list('user_id', flat=True)
    if not userid_list:
        raise BusinessException(ERR_USERID_ERROR)

    users = User.objects.filter(id__in=userid_list, area__area_level=int(area_level), del_flag=FALSE_INT)
    if not users:
        # 如果这里异常有可能调用这个函数前面的程序有问题。
        raise BusinessException(ERR_USER_NOAREA_PERMISSION)
    return users.first().area


def is_superuser(account, activity_id):
    # 检查用户是否是传入项目的超管
    user_info = get_account_activity_role(activity_id, account.id)
    if USER_TYPE_ACTIVITY_ADMIN in user_info:
        return True
    else:
        return False


def get_curuser_by_id(cur_user_id):
    cur_user = User.objects.get(id=cur_user_id, del_flag=FALSE_INT)
    return cur_user


def get_areaname_by_id(area_id):
    area = Area.objects.get(id=area_id)
    # 非直属直接返回地区名称
    if area.manage_direct == 0:
        return area.area_name

    # 直属的，先判断地区层级，如果是市级，则返回省直属，如果是区县级，则返回市直属
    if area.area_level == LEVEL_CITY:
        return u'省直属'
    return u'市直属'


def _get_areadetail_by_id(area_id):
    # 通过area_id查询对应的市州、区县、机构、直属信息。
    nation = ''
    province = ''
    city = ''
    country = ''
    institution = ''
    manage_direct = ''

    area_id_institution = ''
    area_id_country = ''
    area_id_city = ''
    area_id_province = ''
    area_id_nation = ''

    cur_area_id = area_id
    first_row = True
    whiletimes = 0
    while True:
        # 搞个限制，万一配置错误，也不会导致死循环。
        whiletimes += 1
        if whiletimes > 8:
            logger.error(u'发现area表中可能存在层级过多的配置错误。area_id=%s' % cur_area_id)
            break

        area = Area.objects.get(id=cur_area_id)

        if area.area_level == LEVEL_CITY:
            city = area.area_name
            area_id_city = area.id
        elif area.area_level == LEVEL_COUNTY:
            country = area.area_name
            area_id_country = area.id
        elif area.area_level == LEVEL_INSTITUTION:
            institution = area.area_name
            area_id_institution = area.id
        elif area.area_level == LEVEL_PROVINCE:
            province = area.area_name
            area_id_province = area.id
        elif area.area_level == LEVEL_NATION:
            nation = area.area_name
            area_id_nation = area.id
        else:
            pass

        # 第一次循环，检查是不是直属
        if first_row:
            first_row = False
            manage_direct = area.manage_direct

            if area.manage_direct == 1:
                institution = area.area_name
                if area.area_level == LEVEL_CITY:
                    city = u'省直属'
                elif area.area_level == LEVEL_COUNTY:
                    country = u'市直属'
                elif area.area_level == LEVEL_PROVINCE:
                    province = u'国直属'
                else:
                    pass

        # 如果没有父节点，跳出循环
        if not area.parent_id:
            break
        else:
            cur_area_id = area.parent_id

    result = {
        "area_id": area_id,
        "nation": nation,
        "province": province,
        "city": city,
        "country": country,
        "institution": institution,
        "manage_direct": manage_direct,
        "area_id_institution": area_id_institution,
        "area_id_country": area_id_country,
        "area_id_city": area_id_city,
        "area_id_province": area_id_province,
        "area_id_nation": area_id_nation,
    }
    return result


KEY_AREA_Q_COUNT = 'area_detail_query'
KEY_AREA_Q_HIT_COUNT = 'area_detail_query_hit'
KEY_AREA_Q_MISS_COUNT = 'area_detail_query_miss'

def get_areadetail_by_id(area_id):
    if not cache.get(KEY_AREA_Q_COUNT):
        cache.set(KEY_AREA_Q_COUNT, 1)
    else:
        cache.incr(KEY_AREA_Q_COUNT)
    key = 'area_detail_%s' % area_id
    if not cache.get(key):
        logger.info('cache area detail for ID:%s' % area_id)
        cache.set(key, _get_areadetail_by_id(area_id))
        if not cache.get(KEY_AREA_Q_MISS_COUNT):
            cache.set(KEY_AREA_Q_MISS_COUNT, 1)
        else:
            cache.incr(KEY_AREA_Q_MISS_COUNT)
        logger.info('get_areadetail_by_id cache MISS! rate: %s / %s'
                    % (cache.get(KEY_AREA_Q_MISS_COUNT), cache.get(KEY_AREA_Q_COUNT)))
    else:
        if not cache.get(KEY_AREA_Q_HIT_COUNT):
            cache.set(KEY_AREA_Q_HIT_COUNT, 1)
        else:
            cache.incr(KEY_AREA_Q_HIT_COUNT)
        logger.info('get_areadetail_by_id cache HIT! rate: %s / %s'
                    % (cache.get(KEY_AREA_Q_HIT_COUNT), cache.get(KEY_AREA_Q_COUNT)))
    return cache.get(key)


def cache_areadetail_by_id():
    qs = Area.objects.filter(del_flag=FALSE_INT)
    count = qs.count()
    for i, each in enumerate(qs):
        get_areadetail_by_id(each.id)
        logger.info('cached area %s detail, progress: %s / %s' % (each.id, i+1, count))


# 根据区域节点id，查询直接孩子列表
def get_child_by_areaid(area_id, manage_direct=None):
    # 查询所有市州列表, manage_direct为1时查询直属，为0时查询非直属，为空时都查询
    result = []
    my_area = Area.objects.get(del_flag=FALSE_INT, id=area_id)
    my_area_level = my_area.area_level

    areas = Area.objects.filter(del_flag=FALSE_INT, parent_id=area_id)
    if manage_direct:
        areas = areas.filter(manage_direct=manage_direct)

    for each_area in areas:
        result_row = {
            "area_id": each_area.id,
            "area_name": each_area.area_name,
            "manage_direct": each_area.manage_direct,
        }
        result.append(result_row)

        # if not area_level:
        #     area_level = each_area.area_level

    # 当查询非直属时，在列表最后拼上直属标识。
    if manage_direct == 0 or manage_direct == "0":
        if my_area_level == LEVEL_PROVINCE:
            result_row = {
                "area_id": "",
                "area_name": u"省直属",
                "manage_direct": 1,
            }
            result.append(result_row)
        elif my_area_level == LEVEL_CITY:
            result_row = {
                "area_id": "",
                "area_name": u"市直属",
                "manage_direct": 1,
            }
            result.append(result_row)
    return result


# 通过中文随机查询下级一个地区的名称列表
def get_rank_child_area_name(area_name, area_level):
    result = []
    areas = Area.objects.filter(parent__area_name=area_name, parent__area_level=area_level, parent__del_flag=FALSE_INT, del_flag=FALSE_INT)
    for each_area in areas:
        result.append(each_area.area_name)

    if area_level == LEVEL_NATION:
        result.append(u'国直属')
    if area_level == LEVEL_PROVINCE:
        result.append(u'省直属')
    if area_level == LEVEL_CITY:
        result.append(u'市直属')
    return result


def get_regiondetail_by_id(region_id):
    # 通过region_id查询对应的市州、区县、机构、直属信息。
    nation = ''
    province = ''
    city = ''
    country = ''
    institution = ''

    cur_region_id = region_id
    first_row = True
    whiletimes = 0
    while True:
        # 搞个限制，万一配置错误，也不会导致死循环。
        whiletimes += 1
        if whiletimes > 8:
            logger.error(u'发现area表中可能存在层级过多的配置错误。region_id=%s' % cur_region_id)
            break

        region = Region.objects.get(id=cur_region_id)

        if region.region_level == LEVEL_CITY:
            city = region.region_name
        elif region.region_level == LEVEL_COUNTY:
            country = region.region_name
        elif region.region_level == LEVEL_INSTITUTION:
            institution = region.region_name
        elif region.region_level == LEVEL_PROVINCE:
            province = region.region_name
        elif region.region_level == LEVEL_NATION:
            nation = region.region_name
        else:
            pass

        # 如果没有父节点，跳出循环
        if not region.parent_id:
            break
        else:
            cur_region_id = region.parent_id

    result = {
        "region_id": region_id,
        "nation": nation,
        "province": province,
        "city": city,
        "country": country,
        "institution": institution,
    }
    return result


def area_by_pov(area, pov):
    # 从观察者视角获取Area
    a = area
    ap = a.parent
    while ap != None:
        if pov and ap == pov:
            return a
        a = ap
        ap = ap.parent
    return area


def area_name(area_id, joint='', full=True, pov=None, ignore_china=True):
    """
        full：是否显示从顶级到此area的区域全名
        pov : 观察者视角（Area）
    """
    if not pov:
        key = 'areaname_' + str(area_id) + '*' + joint + '*' + bool2str(full)
    else:
        key = 'areaname_' + str(area_id) + '*' + joint + '*' + bool2str(full) + '*' + str(pov.area_level)
    if not cache.get(area_id):
        d = get_areadetail_by_id(area_id)
        zone = ('nation', 'province', 'city', 'country', 'institution')
        zone_lv_map = {0:16, 1:8, 2:4, 3:2, 4:1}
        direct = (u'国直属', u'省直属', u'市直属')
        result = ''
        endpoint = ''
        for i, z in enumerate(zone):
            if pov and (zone_lv_map[i] < pov.area_level / 2):
                break
            if ignore_china and i == 0:
                if Area.objects.filter(id=int(area_id)).first().area_level != LEVEL_NATION:
                    continue
            if d[z]:
                if d[z] in direct and z != 'institution':
                    endpoint = u'%s [%s]' % (d['institution'], d[z])
                    result += (endpoint + joint)
                    break
                else:
                    endpoint = d[z]
                    result += (endpoint + joint)
        result = result.strip(joint)
        if not full:
            result = endpoint
        cache.set(key, result)
    return cache.get(key)


def update_area_fullname(area_id):
    # 只更新到机构，机构下
    areas = Area.objects.filter(area_level__gte=LEVEL_INSTITUTION)
    if area_id:
        areas = areas.filter(id=area_id)

    for each_area in areas:
        area_detail = get_areadetail_by_id(each_area.id)
        area_fullname = '%s%s%s%s' % (area_detail['province'], area_detail['city'], area_detail['country'], area_detail['institution'])
        each_area.area_fullname = area_fullname
        each_area.save()

    return 'ok'


def area_bind_region(area):
    # 将地区和region进行绑定，绑定成功返回True，不需要绑定或绑定失败返回False
    if not area:
        return False

    if not area.manage_direct and area.area_level != LEVEL_INSTITUTION:
        return False

    # 检查是否有同名region,如果有则自动将area与region绑定，学校管理员在活动中添加注册用户
    region = Region.objects.filter(region_name=area.area_name, region_level=LEVEL_INSTITUTION, del_flag=FLAG_NO).first()
    if region:
        area.region = region
        area.save()
        return True
    return False

