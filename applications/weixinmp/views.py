# coding=utf-8
import hashlib
import uuid
from urllib import urlencode

import requests
from django.contrib import auth
from django.contrib.auth.models import AnonymousUser
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseForbidden
from django.shortcuts import render_to_response
from django.conf import settings
from applications.weixinmp.agents import get_weixin_define
from applications.weixinmp.models import WeixinShortUrl, WeixinAccount, WeixinScanConfirm
from utils.check_auth import validate
from utils.check_param import getp, InvalidHttpParaException
from utils.const_def import FLAG_NO, FALSE_INT, WEIXIN_SCAN_TYPE_OLDUSERBIND
from utils.const_err import SUCCESS
from utils.net_helper import response_exception, response200, get_url_domain, response_parameter_error, get_cur_domain, get_url_qs
from utils.public_fun import send_http_request, convert_to_url_path
from utils.utils_log import log_response, log_request
from . import agents
import logging
import json
import traceback

logger = logging.getLogger(__name__)


def wx_get_code(request):
    try:
        state = request.GET.get("state", "")
        confirm_code = request.GET.get("confirm_code", "")
        weixindefine = get_weixin_define(settings.WEIXIN_DEFINECODE_JS)

        if not weixindefine:
            return HttpResponseForbidden(u'<h1>Forbidden<br/> 获取竞赛网公众号信息失败，请从手机端扫码登陆使用本系统</h1>')

        weixin_scope = 'snsapi_base' if weixindefine.only_request_openid else 'snsapi_userinfo'

        cur_domain = get_cur_domain(request)
        state = get_shorturl_id(state)['id']
        # logger.info(dir(settings))
        param_dict = {
            "appid": weixindefine.app_id,
            "redirect_uri": 'http://%s%s' % (cur_domain, settings.WEIXIN_REDIRECT_URI),
            "response_type": "code",
            "scope": weixin_scope,
            "state": state,
            "confirm_code": confirm_code,
        }
        param_str = urlencode(param_dict)
        redirect_uri = "https://open.weixin.qq.com/connect/oauth2/authorize?%s#wechat_redirect" % param_str
        logger.debug(redirect_uri)

        return HttpResponseRedirect(redirect_uri)
    except Exception as ex:
        sErrInfo = traceback.format_exc()
        logger.error(sErrInfo)
        logger.error(ex.message)
        return HttpResponseForbidden(ex.message)


def wx_code_to_access_token(request):
    try:
        code = request.GET.get("code")
        state = request.GET.get("state")
        # confirm_code = request.GET.get("confirm_code", "")
        weixindefine = get_weixin_define(settings.WEIXIN_DEFINECODE_JS)
        if not weixindefine:
            return HttpResponseForbidden(u'<h1>Forbidden<br/> 获取公众号信息失败</h1>')

        state = get_orginurl(shorturl_id=state, del_indb=False)['origin_url']
        qs_dict = get_url_qs(state)
        logger.info('qs_dict=%s' % qs_dict)
        confirm_code = qs_dict.get('confirm_code', [''])[0]
        logger.info('confirm_code=%s' % confirm_code)
        param_dict = {
            "appid": weixindefine.app_id,
            "secret": weixindefine.app_secret,
            "code": code,
            "grant_type": "authorization_code"
        }
        param_str = urlencode(param_dict)
        uri = "https://api.weixin.qq.com/sns/oauth2/access_token?%s" % param_str
        logger.debug(uri)
        data_str = send_http_request(url=uri, method="GET")
        logger.debug(data_str)
        data = json.loads(data_str)
        if "errcode" in data or "openid" not in data or not data["openid"]:
            logger.error(uri)
            logger.error(data_str)
            return HttpResponseForbidden(data_str)

        account = agents.get_account_byjsopenid(data["openid"])

        # 检查是否是学校码扫码进来的，如果是扫码且没有绑定，则获取到openid后，将openid跳转到家长绑定的页面，如果已经绑定，则跳转到学校首页
        # state_url = convert_to_url_path(state)
        # if 'wx/page/scan/schoolcode?sid=' in state_url:
        #     if not account:
        #         return HttpResponseRedirect("/m/register/enrollParent?sid=%s&openid=%s" % (school_id, data["openid"]))
        #     else:
        #         return HttpResponseRedirect("/m?sid=%s" % school_id)

        # 检查是否是家长邀请码扫码进来的，则获取到openid后，将openid跳转到家长绑定的页面
        # if 'wx/page/scan/parentcode?sid=' in state_url:
        #     params_get = state_url[state_url.find('?')+1:]  # ?后面的所有参数
        #     return HttpResponseRedirect("/m/personal/parent/addParent?%s&openid=%s" % (params_get, data["openid"]))

        # 检查是否是个人中心添加角色跳转过来
        # if 'wx/page/add/role?sid=' in state_url:
        #     if not account:
        #         return HttpResponseForbidden(u'<h1>Forbidden<br/> 请从个人中心=》添加角色页页进入。</h1>')
        #     else:
        #         account_mobile = account.mobile
        #         address = ''  # get_account_address(account)
        #         params_get = state_url[state_url.find('?')+1:]  # ?后面的所有参数
        #         return HttpResponseRedirect("/m/register/identify?%s&openid=%s&mobile=%s&add=%s" % (params_get, data["openid"], account_mobile, address))

        # 检查用户是否关注公众号
        weixin_global_access_token = agents.get_weixin_global_access_token(weixindefine)
        if weixindefine.force_follow:
            uri = 'https://api.weixin.qq.com/cgi-bin/user/info?access_token=%s&openid=%s&lang=zh_CN' % (weixin_global_access_token, data["openid"])
            logger.debug(uri)
            wx_userinfo_str = send_http_request(url=uri, method="GET")
            logger.debug(wx_userinfo_str)
            wx_userinfo = json.loads(wx_userinfo_str)
            if "errcode" in wx_userinfo or "subscribe" not in wx_userinfo:
                logger.error(uri)
                logger.error(wx_userinfo_str)
                return HttpResponseForbidden(wx_userinfo_str)

            if wx_userinfo["subscribe"] == 0:
                if weixindefine.mp_image_url:
                    return HttpResponseRedirect(weixindefine.mp_image_url)
                else:
                    return HttpResponseForbidden(u'<h1>Forbidden<br/> 使用系统前，请先关注%s微信公众号</h1>' % weixindefine.school.name_full)

        # 如果是老用户绑定微信
        if 'wx/page/scan' in state:

            params = {
                "openid": data["openid"],
                "confirm_code": confirm_code,
            }
            # return render_to_response("m/register/identify?sid=" + school_id, params)
            # return HttpResponseRedirect("/m/register/identify?sid=%s&openid=%s" % (school_id, data["openid"]), params)
            # 增加绑定时，拿烽火openid,更新confirmcode对应的
            # state = 'http%%3A%%2F%%2F%s%%2Fm%%2Fregister%%2Fidentify%%3Fsid%%3D%s%%26openid%%3D%s' % (request.META.get('HTTP_HOST', ""), school_id, data["openid"])
            weixinconfirm = WeixinScanConfirm.objects.filter(code=confirm_code, del_flag=FALSE_INT).first()
            if not weixinconfirm:
                return HttpResponseForbidden(u'<h1>Forbidden<br/> 二维码已失效，请刷新二维码</h1>')

            weixinconfirm.openid = data["openid"]
            weixinconfirm.save()
            return HttpResponseRedirect("/wx/authorize_fh?state=%s&confirm_code=%s" % (state, confirm_code))

        if not weixindefine.only_request_openid:
            # 获取并更新用户信息
            # account = wx_get_userinfo(data["access_token"], data["openid"], school_id)
            # if not account:
            #     return HttpResponseForbidden()

            # 更新用户信息
            wx_update_weixinaccount(data["access_token"], data["openid"], account.id)

        # 如果原请求中没有openid，则在原state后面拼接openid
        if state.find('openid=') < 0:
            if state.find('?') >= 0:
                state = '%s&openid=%s' % (state, data["openid"])
            else:
                state = '%s?openid=%s' % (state, data["openid"])

        # 登录单系统
        # account.backend = settings.AUTHENTICATION_BACKENDS[1]
        # auth.login(request, account)
        redirect_uri = convert_to_url_path(state)

        return HttpResponseRedirect(redirect_uri)
    except Exception as ex:
        sErrInfo = traceback.format_exc()
        logger.error(sErrInfo)
        logger.error(ex.message)
        return HttpResponseForbidden(ex.message)


def wx_get_code_fh(request):
    try:
        state = request.GET.get("state", "")
        confirm_code = request.GET.get("confirm_code", "")
        fh_weixindefine = get_weixin_define(settings.WEIXIN_DEFINECODE_FH)

        if not fh_weixindefine:
            return HttpResponseForbidden(u'<h1>Forbidden<br/> 烽火公众号系统异常，请联系系统管理员！</h1>')

        weixin_scope = 'snsapi_base'

        cur_domain = get_cur_domain(request)
        state = get_shorturl_id(state)['id']
        param_dict = {
            "appid": fh_weixindefine.app_id,
            "redirect_uri": 'http://%s%s' % (cur_domain, settings.WEIXIN_REDIRECT_URI_FH),  # settings.weixin_redirect_uri
            "response_type": "code",
            "scope": weixin_scope,
            "state": state,
            "confirm_code": confirm_code,
        }
        param_str = urlencode(param_dict)
        redirect_uri = "https://open.weixin.qq.com/connect/oauth2/authorize?%s#wechat_redirect" % param_str
        logger.debug(redirect_uri)

        return HttpResponseRedirect(redirect_uri)
    except Exception as ex:
        sErrInfo = traceback.format_exc()
        logger.error(sErrInfo)
        logger.error(ex.message)
        return HttpResponseForbidden(ex.message)


def wx_code_to_access_token_fh(request):
    try:
        code = request.GET.get("code")
        state = request.GET.get("state")
        fh_weixindefine = get_weixin_define(settings.WEIXIN_DEFINECODE_FH)
        if not fh_weixindefine:
            return HttpResponseForbidden(u'<h1>Forbidden<br/> 烽火公众号系统异常，请联系系统管理员！</h1>')

        state = get_orginurl(state)['origin_url']
        qs_dict = get_url_qs(state)
        logger.info('qs_dict=%s' % qs_dict)
        confirm_code = qs_dict.get('confirm_code', [''])[0]

        param_dict = {
            "appid": fh_weixindefine.app_id,
            "secret": fh_weixindefine.app_secret,
            "code": code,
            "grant_type": "authorization_code"
        }
        param_str = urlencode(param_dict)
        uri = "https://api.weixin.qq.com/sns/oauth2/access_token?%s" % param_str
        logger.debug(uri)
        data_str = send_http_request(url=uri, method="GET")
        logger.debug(data_str)
        data = json.loads(data_str)
        if "errcode" in data or "openid" not in data or not data["openid"]:
            logger.error(uri)
            logger.error(data_str)
            return HttpResponseForbidden(data_str)

        account = agents.get_account_byfhopenid(data["openid"])
        weixinconfirm = WeixinScanConfirm.objects.filter(code=confirm_code, del_flag=FALSE_INT).first()
        if not weixinconfirm:
            return HttpResponseForbidden(u'<h1>Forbidden<br/> 二维码已失效，请刷新二维码</h1>')

        weixinconfirm.openid_fh = data["openid"]
        weixinconfirm.save()

        # 如果已经绑定，直接记录用户openid, 不请求用户其它资料，可以对用户免打扰。
        if not isinstance(request.user, AnonymousUser):
            WeixinAccount.objects.filter(account=request.user, del_flag=FLAG_NO).update(openid_fh=data["openid"])

        # 如果原请求中没有openid_fh，则在原state后面拼接openid_fh
        if state.find('openid_fh=') < 0:
            if state.find('?') >= 0:
                state = '%s&openid_fh=%s' % (state, data["openid"])
            else:
                state = '%s?openid_fh=%s' % (state, data["openid"])

        redirect_uri = convert_to_url_path(state)
        return HttpResponseRedirect(redirect_uri)
    except Exception as ex:
        sErrInfo = traceback.format_exc()
        logger.error(sErrInfo)
        logger.error(ex.message)
        return HttpResponseForbidden(ex.message)


def wx_get_code_fhlogin(request):
    try:
        state = request.GET.get("state", "")
        fh_weixindefine = get_weixin_define(settings.WEIXIN_DEFINECODE_FH)

        if not fh_weixindefine:
            return HttpResponseForbidden(u'<h1>Forbidden<br/> 烽火公众号系统异常，请联系系统管理员！</h1>')

        weixin_scope = 'snsapi_base'

        cur_domain = get_cur_domain(request)
        state = get_shorturl_id(state)['id']
        param_dict = {
            "appid": fh_weixindefine.app_id,
            "redirect_uri": 'http://%s%s' % (cur_domain, settings.WEIXIN_REDIRECT_URI_FHLOGIN),  # settings.weixin_redirect_uri
            "response_type": "code",
            "scope": weixin_scope,
            "state": state,
        }
        param_str = urlencode(param_dict)
        redirect_uri = "https://open.weixin.qq.com/connect/oauth2/authorize?%s#wechat_redirect" % param_str
        logger.debug(redirect_uri)

        return HttpResponseRedirect(redirect_uri)
    except Exception as ex:
        sErrInfo = traceback.format_exc()
        logger.error(sErrInfo)
        logger.error(ex.message)
        return HttpResponseForbidden(ex.message)


def wx_code_to_access_token_fhlogin(request):
    try:
        code = request.GET.get("code")
        state = request.GET.get("state")
        fh_weixindefine = get_weixin_define(settings.WEIXIN_DEFINECODE_FH)
        if not fh_weixindefine:
            return HttpResponseForbidden(u'<h1>Forbidden<br/> 烽火公众号系统异常，请联系系统管理员！</h1>')

        state = get_orginurl(state)['origin_url']
        param_dict = {
            "appid": fh_weixindefine.app_id,
            "secret": fh_weixindefine.app_secret,
            "code": code,
            "grant_type": "authorization_code"
        }
        param_str = urlencode(param_dict)
        uri = "https://api.weixin.qq.com/sns/oauth2/access_token?%s" % param_str
        logger.debug(uri)
        data_str = send_http_request(url=uri, method="GET")
        logger.debug(data_str)
        data = json.loads(data_str)
        if "errcode" in data or "openid" not in data or not data["openid"]:
            logger.error(uri)
            logger.error(data_str)
            return HttpResponseForbidden(data_str)

        # 拿到openid后，找到对应的account，使用cas登陆
        account = agents.get_account_byfhopenid(data["openid"])
        if not account:
            return HttpResponseForbidden(u'<h1>Forbidden<br/> 请先通过学校的公众号绑定帐号！</h1>')

        # 测试登录单系统
        account.backend = settings.AUTHENTICATION_BACKENDS[1]
        auth.login(request, account)
        redirect_uri = convert_to_url_path(state)

        return HttpResponseRedirect(redirect_uri)
    except Exception as ex:
        sErrInfo = traceback.format_exc()
        logger.error(sErrInfo)
        logger.error(ex.message)
        return HttpResponseForbidden(ex.message)


def wx_pc_scanlogin(request):
    try:
        code = request.GET.get("code")
        state = request.GET.get("state")
        fh_weixindefine = get_weixin_define(settings.WEIXIN_DEFINECODE_FH)
        if not fh_weixindefine:
            return HttpResponseForbidden(u'<h1>Forbidden<br/> 烽火公众号系统异常，请联系系统管理员！</h1>')

        # 到cas查询state有效性(不查了)
        # cas_state_check_url = "%sqrcode/status?q=%s" % (settings.CAS_SERVER_URL, state)
        # try:
        #     data_str = send_http_request(url=cas_state_check_url, method="GET")
        # except Exception as e:
        #     return HttpResponseForbidden(u'<h1>Forbidden<br/> 二维码错误，请重新刷新二维码！</h1>')  #  需要前端做一个新的页面返回到用户手机上。

        # state = get_orginurl(state)['origin_url']
        param_dict = {
            "appid": fh_weixindefine.app_id,
            "secret": fh_weixindefine.app_secret,
            "code": code,
            "grant_type": "authorization_code"
        }
        param_str = urlencode(param_dict)
        uri = "https://api.weixin.qq.com/sns/oauth2/access_token?%s" % param_str
        logger.debug(uri)
        data_str = send_http_request(url=uri, method="GET")
        logger.debug(data_str)
        data = json.loads(data_str)
        if "errcode" in data or "openid" not in data or not data["openid"]:
            logger.error(uri)
            logger.error(data_str)
            return HttpResponseForbidden(data_str)

        # 拿到openid后，找到对应的account，使用cas登陆
        account = agents.get_account_byfhopenid(data["openid"])
        if not account:
            # 通知cas，用于前端显示。
            cas_state_upgrade_url = "http://%s/qrcode/status/upgrade?q=%s&username=" % (get_url_domain(settings.CAS_SERVER_URL), state)
            logger.debug(cas_state_upgrade_url)
            # data_str = send_http_request(url=cas_state_upgrade_url, method="GET")
            data_str = requests.get(cas_state_upgrade_url)

            # return HttpResponseForbidden(u'<h1>Forbidden<br/> 请先通过学校的公众号绑定帐号！</h1>')
            return HttpResponseRedirect('/page/scan/result/pc?c=30')
            # return render_to_response("index.html")

        # 记录表（openid,state,生成新的token,account_id,account_username）
        confirm_code = uuid.uuid4().hex
        weixinscanconfirm = WeixinScanConfirm()
        weixinscanconfirm.code = confirm_code
        weixinscanconfirm.state = state
        weixinscanconfirm.openid = data["openid"]
        weixinscanconfirm.account = account
        weixinscanconfirm.save()
        # return HttpResponseForbidden(u'<h1>Forbidden<br/> confirm_code = %s</h1>' % confirm_code)
        return HttpResponseRedirect('/page/scan/confirm/pc?confirm_code=%s' % confirm_code)
    except Exception as ex:
        sErrInfo = traceback.format_exc()
        logger.error(sErrInfo)
        logger.error(ex.message)
        return HttpResponseForbidden(ex.message)


def wx_update_weixinaccount(access_token, openid, account_id):
    try:
        param_dict = {
            "access_token": access_token,
            "openid": openid,
            "lang": "zh_CN",
        }
        param_str = urlencode(param_dict)
        uri = "https://api.weixin.qq.com/sns/userinfo?%s" % param_str
        logger.debug(uri)
        data_str = send_http_request(url=uri, method="GET")
        logger.debug(data_str)
        data = json.loads(data_str)
        if "errcode" in data or "openid" not in data or not data["openid"]:
            logger.error(uri)
            logger.error(data_str)
            return None
        # print data
        wx_openid = data["openid"]
        wx_nickname = data["nickname"]
        wx_sex = data["sex"]
        wx_province = data["province"]
        wx_city = data["city"]
        wx_country = data["country"]
        wx_headimgurl = data["headimgurl"]
        wx_unionid = data.get("unionid", "")

        weixinaccount = WeixinAccount.objects.get(openid=wx_openid, account_id=account_id, del_flag=FLAG_NO)
        if not weixinaccount:
            raise Exception(u'系统异常，获取微信用户信息失败！')

        weixinaccount.name = wx_nickname
        weixinaccount.sex = wx_sex
        weixinaccount.province = wx_province
        weixinaccount.city = wx_city
        weixinaccount.country = wx_country
        weixinaccount.image_url = wx_headimgurl
        weixinaccount.unionid = wx_unionid
        weixinaccount.save()

        return
    except Exception as ex:
        logger.exception(ex)
        return response_exception(ex, ex.message)


def wx_get_verifyfile(request):
    filedata = 'jIjfmE2UW1zSOJPc'
    response = HttpResponse(filedata)
    response['Content-Type'] = 'application/octet-stream'
    response['Content-Disposition'] = 'attachment;filename="MP_verify_jIjfmE2UW1zSOJPc.txt"'
    return response


def wx_get_jswverifyfile(request):
    filedata = 'ySQKawRcgCbi0lzA'
    response = HttpResponse(filedata)
    response['Content-Type'] = 'application/octet-stream'
    response['Content-Disposition'] = 'attachment;filename="MP_verify_ySQKawRcgCbi0lzA.txt"'
    return response


def get_weixin_global_access_token(request):
    log_request(request)
    weixin_define_code = request.GET.get("weixin_define_code", "")
    weixin_app_id = request.GET.get("appid", "")

    try:
        weixindefine = get_weixin_define(weixin_define_code, weixin_app_id)
        cur_access_token = agents.get_weixin_global_access_token(weixindefine)
    except Exception as ex:
        logger.exception(ex)
        return response_exception(ex, ex.message)
    log_response(request, cur_access_token)

    return response200(cur_access_token)


def update_weixin_global_access_token(request):
    weixin_define_code = request.GET.get("weixin_define_code", "")
    weixin_app_id = request.GET.get("appid", "")

    try:
        weixindefine = get_weixin_define(weixin_define_code, weixin_app_id)
        globalaccesstokeninfo = agents.update_weixin_global_access_token(weixindefine)
    except Exception as ex:
        logger.exception(ex)
        return response_exception(ex, ex.message)
    log_response(request, globalaccesstokeninfo)

    return response200({'c': SUCCESS[0], 'm': SUCCESS[1], 'd': globalaccesstokeninfo})


def get_shorturl_id(url, short_url='', add_id_2_shorturl=True):
    # 获取短地址， add_id_2_shorturl 表示将新的短地址数据库记录的的id，拼接到shorturl后面。
    md5str = get_md5(url)
    weixinshorturl = WeixinShortUrl.objects.filter(md5=md5str, del_flag=FLAG_NO).first()

    if not weixinshorturl:
        weixinshorturl = WeixinShortUrl()
        weixinshorturl.origin_url = url
        weixinshorturl.md5 = md5str
        weixinshorturl.save()
        weixinshorturl.short_url = short_url + str(weixinshorturl.id) if add_id_2_shorturl and weixinshorturl.id else short_url
        weixinshorturl.save()

    result = {
        "id": weixinshorturl.id,
        "md5": weixinshorturl.md5,
        "short_url": weixinshorturl.short_url,
        "origin_url": weixinshorturl.origin_url,
    }
    return result


def get_orginurl(shorturl_id, shorturl='', md5='', del_indb=False):
    # del_indb 使用后，自动将短记录在数据库中做物理删除，避免无用数据太多。
    weixinshorturl = WeixinShortUrl.objects.filter(del_flag=0)
    if shorturl_id:
        weixinshorturl = weixinshorturl.filter(id=shorturl_id)

    if shorturl:
        weixinshorturl = weixinshorturl.filter(short_url=shorturl)

    if md5:
        weixinshorturl = weixinshorturl.filter(md5=md5)

    if not weixinshorturl:
        return None
    else:
        weixinshorturl = weixinshorturl.first()

    result = {
        "id": weixinshorturl.id,
        "md5": weixinshorturl.md5,
        "short_url": weixinshorturl.short_url,
        "origin_url": weixinshorturl.origin_url,
    }

    if del_indb:
        WeixinShortUrl.objects.filter(id=weixinshorturl.id).delete()

    return result


def get_md5(str_in):
    hl = hashlib.md5()
    hl.update(str_in.encode(encoding='utf-8'))
    md5str = hl.hexdigest()
    return md5str


@validate('GET', auth=False)
def wx_get_qrcode_scan_status(request):
    """
    功能说明: 前端轮询二维码扫码状态
    """
    log_request(request)
    try:
        confirm_code = getp(request.GET.get('confirm_code'), nullable=False, para_intro='确认码')

    except InvalidHttpParaException as ihpe:
        logger.exception(ihpe)
        return response_parameter_error(ihpe)

    try:
        result = agents.wx_get_qrcode_scan_status(request, confirm_code)
    except Exception as e:
        logger.exception(e)
        return response_exception(e)
    log_response(request, result)
    return response200({'c': SUCCESS[0], 'm': SUCCESS[1], 'd': result})


@validate('GET', auth=False)
def wx_get_qrcode(request):
    """
    功能说明: 获取微信扫码的二维码
    """
    log_request(request)
    try:
        busitype = getp(request.GET.get('busitype'), nullable=False, para_intro='业务类型')

    except InvalidHttpParaException as ihpe:
        logger.exception(ihpe)
        return response_parameter_error(ihpe)

    try:
        result = agents.wx_get_qrcode(request, busitype)
    except Exception as e:
        logger.exception(e)
        return response_exception(e)
    log_response(request, result)
    return response200({'c': SUCCESS[0], 'm': SUCCESS[1], 'd': result})


@validate('GET', auth=False)
def wx_update_scan_status(request):
    """
    功能说明: 更新用户扫码状态
    """
    log_request(request)
    try:
        confirm_code = getp(request.GET.get('confirm_code'), nullable=False, para_intro='用户确认码')
        confirm_status = getp(request.GET.get('confirm_status'), nullable=False, para_intro='用户确认状态')

    except InvalidHttpParaException as ihpe:
        logger.exception(ihpe)
        return response_parameter_error(ihpe)

    try:
        result = agents.wx_update_scan_status(request, confirm_code, confirm_status)
    except Exception as e:
        logger.exception(e)
        return response_exception(e)
    log_response(request, result)
    return response200({'c': SUCCESS[0], 'm': SUCCESS[1], 'd': result})


@validate('GET', auth=False)
def wx_page_scan_qrcode(request):
    """
    功能说明: 微信扫码后处理逻辑，用于更新状态，跳转到相应业务页面
    """
    log_request(request)
    try:
        confirm_code = getp(request.GET.get('confirm_code'), nullable=False, para_intro='用户确认码')
        # busitype = getp(request.GET.get('busitype'), nullable=False, para_intro='业务类型')

    except InvalidHttpParaException as ihpe:
        logger.exception(ihpe)
        return response_parameter_error(ihpe)

    try:
        result = agents.wx_page_scan_qrcode(request, confirm_code)
    except Exception as e:
        logger.exception(e)
        return response_exception(e)
    # log_response(request, result)
    # return response200({'c': SUCCESS[0], 'm': SUCCESS[1], 'd': result})
    return result


@validate('GET', auth=False)
def wx_page_scan_sure(request):
    """
    功能说明: 微信扫码后点击了确认后处理逻辑
    """
    log_request(request)
    try:
        confirm_code = getp(request.GET.get('confirm_code'), nullable=False, para_intro='用户确认码')

    except InvalidHttpParaException as ihpe:
        logger.exception(ihpe)
        return response_parameter_error(ihpe)

    try:
        result = agents.wx_page_scan_sure(request, confirm_code)
    except Exception as e:
        logger.exception(e)
        return response_exception(e)
    return result
