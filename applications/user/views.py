# coding=utf-8
import json
import logging
from django.contrib.auth import logout

import services
from applications.upload_resumable.err_code import ERR_SUCCESS
from competition_v3.settings.base import SESSION_COOKIE_AGE
from utils.const_err import *
from utils.check_auth import validate
from utils.public_fun import paging_with_request
from utils.utils_except import BusinessException
from utils.utils_log import log_request, log_response
from utils.check_param import InvalidHttpParaException, getp
from utils.net_helper import response200, response_exception, response_parameter_error, gen_file_reponse

logger = logging.getLogger(__name__)


@validate("POST")
def api_detail_account(request):
    log_request(request)
    try:
        result = services.detail_account(request.user)
    except Exception as ex:
        logger.exception(ex)
        return response_exception(ex, ex.message)
    un = json.dumps(result, ensure_ascii=False)
    # response.set_cookie("username", un) # UnicodeEncodeError!
    un2 = un.encode('utf8')
    import base64
    un3 = base64.b64encode(un)
    # 向cookie中写入用户资料，避免前端重复查询。
    response = response200(dict(c=SUCCESS[0], m=SUCCESS[1], d=[result]))
    response.set_cookie('account', un3, max_age=SESSION_COOKIE_AGE)
    log_response(request, result)
    return response


@validate("POST")
def api_list_user(request):
    # 查询用户在地区下的所有用户，例如我是湖北省用户，则查询结果为湖北省各地市的用户。即用户库
    log_request(request)
    try:
        area_name = getp(request.POST.get("area_name"), u"区域名称", nullable=True)
        name = getp(request.POST.get("name"), u"名字", nullable=True)
        cur_user_id = getp(request.POST.get("cur_user_id"), u"用户id", nullable=False)
        activity_id = getp(request.POST.get("activity_id"), u"活动ID", nullable=True, default='')
        only_can_add = getp(request.POST.get("only_can_add"), u"仅查询可添加到活动中的用户", nullable=True, default='')
        is_show_store = getp(request.POST.get("is_show_store"), u"是否仅查询用户库中数据", nullable=True, default='1')
    except InvalidHttpParaException as ex:
        logger.exception(ex)
        return response_parameter_error(ex)

    try:
        result = services.list_user(request.user, cur_user_id, area_name, name, is_show_store, activity_id, only_can_add)
    except Exception as ex:
        logger.exception(ex)
        return response_exception(ex, ex.message)
    if result['c'] != SUCCESS[0]:
        return response200(result)
    result = paging_with_request(request, result)
    log_response(request, result)
    return response200(result)


@validate("POST", auth=False)
def api_login(request):
    log_request(request)
    try:
        username = getp(request.POST.get("username"), u"用户名", nullable=True)
        password = getp(request.POST.get("password"), u"密码", nullable=True)
        confirm_code = getp(request.POST.get('confirm_code'), nullable=True, para_intro='用户确认码')
    except InvalidHttpParaException as ex:
        logger.exception(ex)
        return response_parameter_error(ex)
    try:
        if confirm_code:
            # 如果传了confirm_code则直接用确认码进行登陆
            if services.api_confirmcode_login(request, confirm_code):
                return response200({"c": SUCCESS[0], "m": SUCCESS[1]})
            else:
                return response200({"c": ERR_LOGIN_FAIL[0], "m": ERR_LOGIN_FAIL[1]})

        if services.login(request, username=username, password=password):
            result = {"c": SUCCESS[0], "m": SUCCESS[1]}
            log_response(request, result)
            response = response200(result)
            # response.set_cookie('account', json.dumps(services.detail_account(request.user), ensure_ascii=False), max_age=SESSION_COOKIE_AGE)
            un = json.dumps(services.detail_account(request.user), ensure_ascii=False)
            # response.set_cookie("username", un) # UnicodeEncodeError!
            un2 = un.encode('utf8')
            import base64
            un3 = base64.b64encode(un)
            # 向cookie中写入用户资料，避免前端重复查询。
            # response.set_cookie('account', un3, max_age=SESSION_COOKIE_AGE)
            return response
        else:
            result = {"c": ERR_LOGIN_FAIL[0], "m": ERR_LOGIN_FAIL[1]}
    except Exception as ex:
        logger.exception(ex)
        return response_exception(ex, ex.message)
    log_response(request, result)
    return response200(result)


@validate("POST")
def api_logout(request):
    log_request(request)
    try:
        logout(request)
        response = response200(dict(c=SUCCESS[0], m=SUCCESS[1]))
        response.delete_cookie('account')
        return response
    except Exception as ex:
        logger.exception(ex)
        return response_exception(ex)
    # log_response(request, {})
    # return response200(dict(c=SUCCESS[0], m=SUCCESS[1]))


@validate("POST", auth=False)
def api_check_username(request):
    log_request(request)
    try:
        username = getp(request.POST.get("username"), u"用户名", nullable=False)
    except InvalidHttpParaException as ex:
        return response_parameter_error(ex)
    try:
        result = services.check_username(request.user, username)
    except Exception as ex:
        logger.exception(ex)
        return response_exception(ex, ex.message)
    log_response(request, result)
    return response200(result)


@validate("POST", auth=True)
def api_add_user(request):
    log_request(request)
    try:
        username = getp(request.POST.get("username"), u"用户名", nullable=False)
        name = getp(request.POST.get("name"), u"名称", nullable=False)
        sex = getp(request.POST.get("sex"), u"性别", nullable=False)
        # area_name = getp(request.POST.get("area_name"), u"地区", nullable=False)
        # current_user_id = getp(request.POST.get("current_user_id"), u'当前用户', nullable=False)
        # manage_direct = getp(request.POST.get("manage_direct"), u"直属标志", nullable=True)
        area_id = getp(request.POST.get("area_id"), u"区域ID", nullable=True)
        direct_area_id = getp(request.POST.get("direct_area_id"), u"哪一个区域直属", nullable=True)
        institution = getp(request.POST.get("institution"), u"组织名称", nullable=True)

    except InvalidHttpParaException as ex:
        logger.exception(ex)
        return response_parameter_error(ex)
    try:
        result = services.add_user(request.user, username, name, sex, area_id, direct_area_id, institution)
    except Exception as ex:
        logger.exception(ex)
        return response_exception(ex, ex.message)
    log_response(request, result)
    return response200(result)


@validate("POST", auth=True)
def api_mod_user(request):
    log_request(request)
    try:
        user_id = getp(request.POST.get("user_id"), u"用户ID", nullable=False)
        username = getp(request.POST.get("username"), u"用户名", nullable=True, default='')  # 暂不允许修改用户名，修改用户视为删除旧用户，增加新用户,但你非要改我也能支持liukai
        name = getp(request.POST.get("name"), u"名称", nullable=False)
        sex = getp(request.POST.get("sex"), u"性别", nullable=False)
        # area_name = getp(request.POST.get("area_name"), u"地区", nullable=False)
        # current_user_id = getp(request.POST.get("current_user_id"), u'当前用户', nullable=False)
        # manage_direct = getp(request.POST.get("manage_direct"), u"直属标志", nullable=True)

        area_id = getp(request.POST.get("area_id"), u"区域ID", nullable=True)
        direct_area_id = getp(request.POST.get("direct_area_id"), u"哪一个区域直属", nullable=True)
        institution = getp(request.POST.get("institution"), u"组织名称", nullable=True)
    except InvalidHttpParaException as ex:
        logger.exception(ex)
        return response_parameter_error(ex)

    try:
        result = services.mod_user(request.user, user_id, username, name, sex, area_id, direct_area_id, institution)
    except Exception as ex:
        logger.exception(ex)
        return response_exception(ex, ex.message)
    log_response(request, result)
    return response200(result)


@validate("POST", auth=True)
def api_reset_others_password(request):
    log_request(request)
    try:
        account_id = getp(request.POST.get('account_id'), u"用户id", nullable=False)
        admin_password = getp(request.POST.get('admin_password'), u"管理员密码")
        new_password = getp(request.POST.get('new_password'), u"新密码")
    except InvalidHttpParaException as ex:
        logger.exception(ex)
        return response_parameter_error(ex)
    try:
        result = services.reset_others_password(user=request.user, account_id=account_id, admin_password=admin_password,
                                                new_password=new_password)
    except Exception as ex:
        logger.exception(ex)
        return response_exception(ex, ex.message)
    log_response(request, result)
    return response200(result)


@validate("POST")
def api_reset_own_password(request):
    log_request(request)
    try:
        old_password = getp(request.POST.get('old_password'), u"原密码")
        new_password = getp(request.POST.get('new_password'), u"新密码")
    except InvalidHttpParaException as ex:
        logger.exception(ex)
        return response_parameter_error(ex)
    try:
        result = services.reset_own_password(user=request.user, old_password=old_password, new_password=new_password)
    except Exception as ex:
        logger.exception(ex)
        return response_exception(ex, ex.message)
    log_response(request, result)
    return response200(result)


@validate("POST")
def api_delete_user(request):
    log_request(request)
    try:
        cur_user_id = getp(request.POST.get("cur_user_id"), u"当前用户的id", nullable=False)
        user_id_list = getp(request.POST.get("user_id_list"), u"删除的用户list", nullable=True)
        area_name = getp(request.POST.get("area_name"), u"区域名称", nullable=True)
        name = getp(request.POST.get("name"), u"名字", nullable=True)
        del_all_user = getp(request.POST.get("del_all_user"), u"是否删除所有用户", nullable=True)

    except InvalidHttpParaException as ex:
        logger.exception(ex)
        return response_parameter_error(ex)
    try:
        result = services.delete_user(request.user, cur_user_id, user_id_list, del_all_user, area_name, name)
    except Exception as ex:
        logger.exception(ex)
        return response_exception(ex, ex.message)
    log_response(request, result)
    return response200(result)


@validate("POST", auth=False)
def api_list_sub_area(request):
    log_request(request)
    try:
        cur_user_id = getp(request.POST.get('cur_user_id'), u"当前用户的id", nullable=True)
        area_id = getp(request.POST.get("area_id"), u"地域id", nullable=True)
        manage_direct = getp(request.POST.get("manage_direct"), u"直属标志", nullable=True)  # 1只查直属，0只查非直属，不传或传空则不限制。
        area_name = getp(request.POST.get("area_name"), u"区域名称", nullable=True)  # 过滤条件，模糊匹配
        is_school = getp(request.POST.get("is_school"), u"是否学校", nullable=True)  # 1只查学校，0只查非学校，不传或传空则不限制。
    except InvalidHttpParaException as ex:
        logger.exception(ex)
        return response_parameter_error(ex)
    try:
        result = services.list_sub_area(request.user, cur_user_id, area_id, manage_direct, area_name, is_school)
    except Exception as ex:
        logger.exception(ex)
        return response_exception(ex, ex.message)
    log_response(request, result)
    return response200(result)


@validate("POST")
def api_config_user(request):
    log_request(request)
    try:
        account_id = getp(request.POST.get("account_id"), u"account_id", nullable=False)
        activity_mask = getp(request.POST.get("activity_mask"), u"可配置的活动掩码", nullable=False)
        area_id = getp(request.POST.get("area_id"), u"创建活动的区域id", nullable=False)
    except InvalidHttpParaException as ex:
        logger.exception(ex)
        return response_parameter_error(ex)
    try:
        result = services.config_user(request.user, account_id, activity_mask, area_id)
    except Exception as ex:
        logger.exception(ex)
        return response_exception(ex, ex.message)
    log_response(request, result)
    return response200(result)


@validate("POST")
def api_add_account(request):
    log_request(request)
    try:
        username = getp(request.POST.get("username"), u"用户名", nullable=False)
        name = getp(request.POST.get("name"), u"姓名", nullable=False)
        sex = getp(request.POST.get("sex"), u"性别", nullable=False)
        activity_mask = getp(request.POST.get("activity_mask"), u"创建活动的掩码", nullable=True)
        area_id = getp(request.POST.get("area_id"), u"区域的id", nullable=True)
    except InvalidHttpParaException as ex:
        logger.exception(ex)
        return response_parameter_error(ex)
    try:
        result = services.add_account(request.user, username, name, sex, activity_mask, area_id)
    except Exception as ex:
        logger.exception(ex)
        return response_exception(ex, ex.message)
    log_response(request, result)
    return response200(result)


@validate("POST")
def api_get_current_user(request):
    log_request(request)
    try:
        area_id = getp(request.POST.get("area_id"), u"地域的id", nullable=True)
    except InvalidHttpParaException as ex:
        logger.exception(ex)
        return response_parameter_error(ex)
    try:
        result = services.get_current_user(request.user, area_id)
    except Exception as ex:
        logger.exception(ex)
        return response_exception(ex, ex.message)
    log_response(request, result)
    return response200(result)


@validate("POST")
def api_get_activity_user(request):
    # 查询某活动中，用户的角色。
    log_request(request)
    try:
        activity_id = getp(request.POST.get("activity_id"), u"活动id", nullable=False)
    except InvalidHttpParaException as ex:
        logger.exception(ex)
        return response_parameter_error(ex)
    try:
        result = services.api_get_activity_user(request.user, activity_id)
    except Exception as ex:
        logger.exception(ex)
        return response_exception(ex, ex.message)
    log_response(request, result)
    return response200({'c': SUCCESS[0], 'm': SUCCESS[1], 'd': result})


@validate("POST", auth=False)
def api_get_area_onhome(request):
    log_request(request)
    try:
        result = services.get_area_onhome()
    except Exception as ex:
        logger.exception(ex)
        return response_exception(ex, ex.message)
    log_response(request, result)
    return response200(result)


@validate("POST", auth=False)
def api_get_area_byid(request):
    log_request(request)
    try:
        area_id = getp(request.POST.get("area_id"), u"地域的id", nullable=True)
    except InvalidHttpParaException as ex:
        logger.exception(ex)
        return response_parameter_error(ex)
    try:
        result = services.get_area_byid(area_id)
    except BusinessException as be:
        logger.exception(be)
        return response_exception(be)
    except Exception as ex:
        logger.exception(ex)
        return response_exception(ex, ex.message)
    log_response(request, result)
    return response200(result)


@validate("POST", auth=False)
def api_import_user(request):
    try:
        file_obj = request.FILES['file']
        cur_user_id = getp(request.POST.get("cur_user_id"), u"当前用户id", nullable=True)
        area_id = getp(request.POST.get("area_id"), u"区域id", nullable=False)
        user_flag = getp(request.POST.get("user_flag"), u"被导入用户的标识（0:普通用户，1:管理员，2:专家）", nullable=False)
    except InvalidHttpParaException as ex:
        logger.exception(ex)
        return response_parameter_error(ex)

    try:
        dictResp = services.import_user(user=request.user, file_obj=file_obj, user_flag=user_flag, area_id=area_id, cur_user_id=cur_user_id)
    except Exception as ex:
        logger.exception(ex)
        return response_exception(ex, ex.message)
    return response200(dictResp)


@validate("POST", auth=False)
def api_import_activity_user(request):
    try:
        file_obj = request.FILES['file']
        activity_id = getp(request.POST.get("activity_id"), u"活动的id", nullable=False)
        cur_user_id = getp(request.POST.get("cur_user_id"), u"当前用户id", nullable=False)
        user_flag = getp(request.POST.get("user_flag"), u"被导入用户的标识（0:普通用户，1:管理员，2:专家）", nullable=True)
    except InvalidHttpParaException as ex:
        logger.exception(ex)
        return response_parameter_error(ex)

    try:
        dictResp = services.import_activity_user(user=request.user, file_obj=file_obj, activity_id=activity_id, user_flag=user_flag, cur_user_id=cur_user_id)
    except Exception as ex:
        logger.exception(ex)
        return response_exception(ex, ex.message)
    return response200(dictResp)


@validate("POST", auth=False)
def api_export_user(request):
    try:
        area_name = getp(request.POST.get("area_name"), u"区域名称", nullable=True)
        name = getp(request.POST.get("name"), u"名字", nullable=True)
        user_id = getp(request.POST.get("user_id"), u"用户id", nullable=False)
        item_id_list = getp(request.POST.get("item_id_list"), u"查询的id列表，JSON", nullable=True)

        result = services.api_export_user(user=request.user, user_id=user_id, area_name=area_name, name=name, item_id_list=item_id_list)
        if result["c"] != ERR_SUCCESS[0]:
            return response200(result)
        file_path = result["d"]
        response = gen_file_reponse(file_path)
        return response

    except Exception as ex:
        logger.exception(ex)
        return response_exception(ex, ex.message)


@validate("POST", auth=False)
def api_export_expert(request):
    try:
        cur_user_id = getp(request.POST.get("cur_user_id"), u"当前用户的id", nullable=False)
        name = getp(request.POST.get("name"), u"姓名", nullable=True)
        area_id = getp(request.POST.get("area_id"), u"地域id", nullable=True)
        manage_direct = getp(request.POST.get("manage_direct"), u"直属标志", nullable=True)
        item_id_list = getp(request.POST.get("item_id_list"), u"查询的id列表，JSON", nullable=True)

        result = services.api_export_expert(user=request.user, cur_user_id=cur_user_id, name=name, area_id=area_id, manage_direct=manage_direct,
                                            item_id_list=item_id_list)
        if result["c"] != ERR_SUCCESS[0]:
            return response200(result)
        file_path = result["d"]
        response = gen_file_reponse(file_path)
        return response

    except Exception as ex:
        logger.exception(ex)
        return response_exception(ex, ex.message)


@validate("POST", auth=False)
def api_export_activity_user(request):
    try:
        cur_user_id = getp(request.POST.get("cur_user_id"), u"当前用户id", nullable=True)
        activity_id = getp(request.POST.get("activity_id"), u"活动的id", nullable=False)
        user_id_list = getp(request.POST.get("user_id_list"), u"用户ID列表", nullable=True, default=[])
        user_flag = getp(request.POST.get("user_flag"), u"被导入用户的标识（0:用户，1:专家）", nullable=True, default=0)
        name = getp(request.POST.get("name"), u"用户名", nullable=True)
        area_id = getp(request.POST.get("area_id"), u"区域ID", nullable=True)
        direct_level = getp(request.POST.get("direct_level"), u"直属等级（4：省直属，2市直属）", nullable=True)
        item_id_list = getp(request.POST.get("item_id_list"), u"查询的id列表，JSON", nullable=True)
        qry_all_user = getp(request.POST.get("qry_all_user"), u"是否查询全部用户", nullable=True)

        if user_id_list:
            account_id_list = json.loads(user_id_list)
        else:
            account_id_list = []

        result = services.export_activity_user(user=request.user, activity_id=activity_id, account_id_list=account_id_list,
                                               name=name, user_flag=user_flag, area_id=area_id, cur_user_id=cur_user_id, direct_level=direct_level,
                                               item_id_list=item_id_list, qry_all_user=qry_all_user)
        if result["c"] != ERR_SUCCESS[0]:
            return response200(result)
        file_path = result["d"]
        response = gen_file_reponse(file_path)
        return response

    except Exception as ex:
        logger.exception(ex)
        return response_exception(ex, ex.message)


@validate("POST", auth=False)
def api_export_activity_expert(request):
    try:
        activity_id = getp(request.POST.get("activity_id"), u"活动的id", nullable=False)
        area_id = getp(request.POST.get("area_id"), u"区域的id", nullable=True)
        name = getp(request.POST.get("name"), u"用户名", nullable=True)
        cur_user_id = getp(request.POST.get("cur_user_id"), u"当前用户的id", nullable=True)
        only_can_add = getp(request.POST.get("only_can_add"), u"是否仅查询可添加的专家", nullable=True)
        direct_level = getp(request.POST.get("direct_level"), u"直属等级（4：省直属，2市直属）", nullable=True)
        institution = getp(request.POST.get("institution"), u"机构名称", nullable=True)
        item_id_list = getp(request.POST.get("item_id_list"), u"查询时的id的JSON列表", nullable=True)

        result = services.export_activity_expert(user=request.user, activity_id=activity_id, area_id=area_id, name=name, cur_user_id=cur_user_id,
                                                 only_can_add=only_can_add, direct_level=direct_level, institution=institution,
                                                 item_id_list=item_id_list)
        if result["c"] != ERR_SUCCESS[0]:
            return response200(result)
        file_path = result["d"]
        response = gen_file_reponse(file_path)
        return response

    except Exception as ex:
        logger.exception(ex)
        return response_exception(ex, ex.message)


@validate("POST", auth=False)
def api_download_user_template(request):
    try:
        user_flag = getp(request.POST.get("user_flag"), u"模板中用户的标识（0:普通用户或管理员，1:专家，默认为0）", nullable=False, default="0")
        area_id = getp(request.POST.get("area_id"), u"模板中用户的标识（0:普通用户或管理员，1:专家，默认为0）", nullable=False, default="0")
        # activity_id = getp(request.POST.get("activity_id"), u"活动的id", nullable=False)

        result = services.download_user_template(user=request.user, area_id=area_id, user_flag=user_flag)
        if result["c"] != ERR_SUCCESS[0]:
            return response200(result)
        file_path = result["d"][0]
        response = gen_file_reponse(file_path)
        return response

    except Exception as ex:
        logger.exception(ex)
        return response_exception(ex, ex.message)


@validate("POST", auth=False)
def api_download_activity_user_template(request):
    try:
        activity_id = getp(request.POST.get("activity_id"), u"活动的id", nullable=True)
        user_flag = getp(request.POST.get("user_flag"), u"模板中用户的标识（0:普通用户或管理员，1:专家，默认为0）", nullable=True, default="0")

        result = services.download_activity_user_template()
        if result["c"] != ERR_SUCCESS[0]:
            return response200(result)
        file_path = result["d"][0]
        response = gen_file_reponse(file_path)
        return response

    except Exception as ex:
        logger.exception(ex)
        return response_exception(ex, ex.message)


@validate("GET", auth=True)
def api_list_account(request):
    log_request(request)
    try:
        name_or_mobile = getp(request.GET.get('name_or_mobile'), nullable=False, para_intro='姓名或手机号')
        rows = getp(request.GET.get('rows'), nullable=True, para_intro='一次返回最大行数')
        page = getp(request.GET.get('page'), nullable=True, para_intro='页码')
        last_id = getp(request.GET.get('last_id'), nullable=True, para_intro='最后id')

    except InvalidHttpParaException as ihpe:
        logger.exception(ihpe)
        return response_parameter_error(ihpe)

    try:
        result = services.api_list_account(request, name_or_mobile, rows, page, last_id)
    except Exception as e:
        logger.exception(e)
        return response_exception(e)
    log_response(request, result)
    return response200({'c': SUCCESS[0], 'm': SUCCESS[1], 'd': result})


@validate("GET", auth=True)
def api_list_account_right(request):
    log_request(request)
    try:
        name_or_mobile = getp(request.GET.get('name_or_mobile'), nullable=True, para_intro='姓名或手机号')
        only_qry_my_right = getp(request.GET.get('only_qry_my_right'), nullable=True, para_intro='仅查询我自己的权限')
        rows = getp(request.GET.get('rows'), nullable=True, para_intro='一次返回最大行数')
        page = getp(request.GET.get('page'), nullable=True, para_intro='页码')
        last_id = getp(request.GET.get('last_id'), nullable=True, para_intro='最后id')

    except InvalidHttpParaException as ihpe:
        logger.exception(ihpe)
        return response_parameter_error(ihpe)

    try:
        result = services.api_list_account_right(request, name_or_mobile, only_qry_my_right, rows, page, last_id)
    except Exception as e:
        logger.exception(e)
        return response_exception(e)
    log_response(request, result)
    return response200({'c': SUCCESS[0], 'm': SUCCESS[1], 'd': result})


@validate("POST", auth=True)
def api_add_account_right(request):
    log_request(request)
    try:
        account_id = getp(request.POST.get('account_id'), nullable=False, para_intro='帐户ID')
        area_id = getp(request.POST.get('area_id'), nullable=False, para_intro='地区ID')

    except InvalidHttpParaException as ihpe:
        logger.exception(ihpe)
        return response_parameter_error(ihpe)

    try:
        result = services.api_add_account_right(request, account_id, area_id)
    except Exception as e:
        logger.exception(e)
        return response_exception(e)
    log_response(request, result)
    return response200({'c': SUCCESS[0], 'm': SUCCESS[1], 'd': result})


@validate("POST", auth=True)
def api_del_account_right(request):
    log_request(request)
    try:
        ids = getp(request.POST.get('ids'), nullable=False, para_intro='ids')  # 英文半角逗号分隔

    except InvalidHttpParaException as ihpe:
        logger.exception(ihpe)
        return response_parameter_error(ihpe)

    try:
        result = services.api_del_account_right(request, ids)
    except Exception as e:
        logger.exception(e)
        return response_exception(e)
    log_response(request, result)
    return response200({'c': SUCCESS[0], 'm': SUCCESS[1], 'd': result})


@validate("POST", auth=False)
def api_account_reg(request):
    log_request(request)
    try:
        name = getp(request.POST.get('name'), nullable=False, para_intro='姓名')
        sex = getp(request.POST.get('sex'), nullable=False, para_intro='性别')
        area_id = getp(request.POST.get('area_id'), nullable=True, para_intro='地区id')
        area_name = getp(request.POST.get("area_name"), u"地域名称", nullable=True)
        manage_direct = getp(request.POST.get("manage_direct"), u"直属标志", nullable=True)
        institution = getp(request.POST.get('institution'), nullable=True, para_intro='机构')
        position = getp(request.POST.get('position'), nullable=True, para_intro='职务')

        region_id = getp(request.POST.get('region_id'), nullable=True, para_intro='区域id')
        email = getp(request.POST.get('email'), nullable=True, para_intro='区域id')

        mobile = getp(request.POST.get('mobile'), nullable=False, para_intro='电话号码')
        smscode = getp(request.POST.get('smscode'), nullable=False, para_intro='短信验证码')
        password = getp(request.POST.get('password'), nullable=False, para_intro='密码')

        is_only_checkparam = getp(request.POST.get('is_only_checkparam'), nullable=True, para_intro='是否仅做参数验证')
        confirm_code = getp(request.POST.get('confirm_code'), nullable=True, para_intro='微信注册确认码')
    except InvalidHttpParaException as ihpe:
        logger.exception(ihpe)
        return response_parameter_error(ihpe)

    try:
        if is_only_checkparam:
            result = services.check_account_reg_param(request, name, sex, area_id, area_name, manage_direct, institution, position, region_id, email,
                                                      mobile, smscode, password, confirm_code)
        else:
            result = services.api_account_reg(request, name, sex, area_id, area_name, manage_direct, institution, position, region_id, email,
                                              mobile, smscode, password, confirm_code)
    except Exception as e:
        logger.exception(e)
        return response_exception(e)
    log_response(request, result)
    return response200({'c': SUCCESS[0], 'm': SUCCESS[1], 'd': result})


@validate("POST", auth=True)
def api_account_dataconfirm(request):
    log_request(request)
    try:
        name = getp(request.POST.get('name'), nullable=False, para_intro='姓名')
        sex = getp(request.POST.get('sex'), nullable=False, para_intro='性别')
        area_id = getp(request.POST.get('area_id'), nullable=True, para_intro='地区id')
        area_name = getp(request.POST.get("area_name"), u"地域名称", nullable=True)
        manage_direct = getp(request.POST.get("manage_direct"), u"直属标志", nullable=True)
        institution = getp(request.POST.get('institution'), nullable=True, para_intro='机构')
        position = getp(request.POST.get('position'), nullable=True, para_intro='职务')

        region_id = getp(request.POST.get('region_id'), nullable=True, para_intro='区域id')
        email = getp(request.POST.get('email'), nullable=True, para_intro='区域id')

    except InvalidHttpParaException as ihpe:
        logger.exception(ihpe)
        return response_parameter_error(ihpe)

    try:
        result = services.api_account_dataconfirm(request, name, sex, area_id, area_name, manage_direct, institution, position, region_id, email)
    except Exception as e:
        logger.exception(e)
        return response_exception(e)
    log_response(request, result)
    return response200({'c': SUCCESS[0], 'm': SUCCESS[1], 'd': result})


@validate("POST", auth=False)
def api_list_region(request):
    log_request(request)
    try:
        region_name = getp(request.POST.get('region_name'), nullable=False, para_intro='区域名称', default='')
        region_level = getp(request.POST.get('region_level'), nullable=False, para_intro='区域层级', default='')
        rows = getp(request.GET.get('rows'), nullable=True, para_intro='一次返回最大行数')
        page = getp(request.GET.get('page'), nullable=True, para_intro='页码')
        last_id = getp(request.GET.get('last_id'), nullable=True, para_intro='最后id')

    except InvalidHttpParaException as ihpe:
        logger.exception(ihpe)
        return response_parameter_error(ihpe)

    try:
        result = services.api_list_region(request, region_name, region_level, rows, page, last_id)
    except Exception as e:
        logger.exception(e)
        return response_exception(e)
    log_response(request, result)
    return response200({'c': SUCCESS[0], 'm': SUCCESS[1], 'd': result})


@validate("POST", auth=False)
def api_update_region_fullname(request):
    log_request(request)
    try:
        region_id = getp(request.POST.get('region_id'), nullable=True, para_intro='区域id', default='')

    except InvalidHttpParaException as ihpe:
        logger.exception(ihpe)
        return response_parameter_error(ihpe)

    try:
        result = services.api_update_region_fullname(region_id)
    except Exception as e:
        logger.exception(e)
        return response_exception(e)
    log_response(request, result)
    return response200({'c': SUCCESS[0], 'm': SUCCESS[1], 'd': result})


@validate("POST", auth=True)
def api_update_area_fullname(request):
    log_request(request)
    try:
        area_id = getp(request.POST.get('area_id'), nullable=True, para_intro='地区id', default='')

    except InvalidHttpParaException as ihpe:
        logger.exception(ihpe)
        return response_parameter_error(ihpe)

    try:
        result = services.api_update_area_fullname(area_id)
    except Exception as e:
        logger.exception(e)
        return response_exception(e)
    log_response(request, result)
    return response200({'c': SUCCESS[0], 'm': SUCCESS[1], 'd': result})


@validate("POST", auth=True)
def api_mod_account(request):
    log_request(request)
    try:
        name = getp(request.POST.get('name'), nullable=False, para_intro='姓名')
        sex = getp(request.POST.get('sex'), nullable=True, para_intro='性别')
        area_id = getp(request.POST.get('area_id'), nullable=True, para_intro='地区id')
        area_name = getp(request.POST.get("area_name"), u"地域名称", nullable=True)
        manage_direct = getp(request.POST.get("manage_direct"), u"直属标志", nullable=True)
        institution = getp(request.POST.get('institution'), nullable=True, para_intro='机构')
        position = getp(request.POST.get('position'), nullable=True, para_intro='职务')

        region_id = getp(request.POST.get('region_id'), nullable=True, para_intro='区域id')
        email = getp(request.POST.get('email'), nullable=True, para_intro='区域id')

        is_self_reg = getp(request.POST.get('is_self_reg'), nullable=True, para_intro='是否自主注册')

    except InvalidHttpParaException as ihpe:
        logger.exception(ihpe)
        return response_parameter_error(ihpe)

    try:
        result = services.api_mod_account(request, name, sex, area_id, area_name, manage_direct, institution, position, region_id, email, is_self_reg)
    except Exception as e:
        logger.exception(e)
        return response_exception(e)
    log_response(request, result)
    return response200({'c': SUCCESS[0], 'm': SUCCESS[1], 'd': result})


@validate("POST", auth=False)
def api_send_smsverifycode(request):
    log_request(request)
    try:
        mobile = getp(request.POST.get('mobile'), nullable=False, para_intro='电话号码')

    except InvalidHttpParaException as ihpe:
        logger.exception(ihpe)
        return response_parameter_error(ihpe)

    try:
        result = services.api_send_smsverifycode(request.user, mobile)
    except Exception as e:
        logger.exception(e)
        return response_exception(e)
    log_response(request, result)
    return response200({'c': SUCCESS[0], 'm': SUCCESS[1], 'd': result})


@validate("POST", auth=False)
def api_check_smsverifycode(request):
    log_request(request)
    try:
        mobile = getp(request.POST.get('mobile'), nullable=False, para_intro='电话号码')
        smscode = getp(request.POST.get('smscode'), nullable=False, para_intro='短信验证码')

    except InvalidHttpParaException as ihpe:
        logger.exception(ihpe)
        return response_parameter_error(ihpe)

    try:
        result = services.api_check_smsverifycode(request.user, mobile, smscode)
    except Exception as e:
        logger.exception(e)
        return response_exception(e)
    log_response(request, result)
    return response200({'c': SUCCESS[0], 'm': SUCCESS[1], 'd': result})


@validate("POST", auth=False)
def api_reset_forget_password(request):
    log_request(request)
    try:
        mobile = getp(request.POST.get('mobile'), nullable=False, para_intro='电话号码')
        smscode = getp(request.POST.get('smscode'), nullable=False, para_intro='短信验证码')
        new_password = getp(request.POST.get('new_password'), nullable=False, para_intro='新密码')

    except InvalidHttpParaException as ihpe:
        logger.exception(ihpe)
        return response_parameter_error(ihpe)

    try:
        result = services.api_reset_forget_password(request.user, mobile, smscode, new_password)
    except Exception as e:
        logger.exception(e)
        return response_exception(e)
    log_response(request, result)
    return response200({'c': SUCCESS[0], 'm': SUCCESS[1], 'd': result})


@validate("POST", auth=False)
def api_qry_institution_reg(request):
    log_request(request)
    try:
        cur_user_id = getp(request.POST.get("cur_user_id"), u"当前用户id", nullable=False)
        rows = getp(request.GET.get('rows'), nullable=True, para_intro='一次返回最大行数')
        page = getp(request.GET.get('page'), nullable=True, para_intro='页码')
        last_id = getp(request.GET.get('last_id'), nullable=True, para_intro='最后id')

    except InvalidHttpParaException as ihpe:
        logger.exception(ihpe)
        return response_parameter_error(ihpe)

    try:
        result = services.api_qry_institution_reg(request.user, cur_user_id, rows, page, last_id)
    except Exception as e:
        logger.exception(e)
        return response_exception(e)
    log_response(request, result)
    return response200({'c': SUCCESS[0], 'm': SUCCESS[1], 'd': result})


@validate("POST", auth=False)
def api_qry_area_dropdowndetail(request):
    log_request(request)
    try:
        area_id = getp(request.POST.get("area_id"), u"地区id", nullable=False)

    except InvalidHttpParaException as ihpe:
        logger.exception(ihpe)
        return response_parameter_error(ihpe)

    try:
        result = services.api_qry_area_dropdowndetail(request.user, area_id)
    except Exception as e:
        logger.exception(e)
        return response_exception(e)
    log_response(request, result)
    return response200({'c': SUCCESS[0], 'm': SUCCESS[1], 'd': result})
