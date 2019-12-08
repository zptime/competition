# coding=utf-8

import logging
from applications.activity.models import Activity, Role
from applications.common.services import area_name

from applications.user.models import User, Area, LEVEL_INSTITUTION, LEVEL_CITY, LEVEL_COUNTY
from utils.const_def import *
from utils.const_err import *
from utils.net_helper import response_parameter_error, response200, response_exception
from utils.check_auth import validate, check
from utils.public_fun import paging_with_request, str_p_datetime
from utils.utils_except import BusinessException
from utils.utils_log import log_response, log_request
from utils.check_param import getp, InvalidHttpParaException

logger = logging.getLogger(__name__)


def area_struct(area):
    from applications.common.services import area_name
    return {
        'area_id': str(area.id),
        'area_level': str(area.area_level),
        'area_is_direct': str(area.manage_direct),
        'area_direct_level': '',
        'area_direct_base': '',
        'area_code': area.area_code,
        'area_name_full': area_name(int(area.id)),
        'area_name_simple': area_name(int(area.id), full=False),
    }


def expert(expert):
    return {
        "expert_id": str(expert.id),
        "account_id": str(expert.account.id),
        "username": expert.account.username,
        "name": expert.name,
        "sex": expert.sex,
        "area_name_full": area_name(str(expert.area.id)),
        "area_name_simple": area_name(str(expert.area.id), full=False),
        "area_id": str(expert.area_id),
        "position": expert.position,
        "is_data_confirm": str(expert.account.is_data_confirm),
    }


def is_activity_owner(activity, account):
    if not activity or not activity.user:
        return None
    elif activity.user.account == account:
        return activity.user
    else:
        return None


def is_devops(account):
    return account.auth != 0


def china():
    return Area.objects.filter(del_flag=FALSE_INT, parent__isnull=True).first()



