# coding=utf-8
import json
import logging

import cStringIO

import datetime

import uuid
from urllib import urlencode

import qrcode
import base64

import sys
from django.conf import settings
from django.db import transaction
from django.http import HttpResponseRedirect

from applications.weixinmp.models import WeixinDefine, WeixinAccount, WeixinScanConfirm
from utils.const_def import *
from utils.const_err import *
from utils.net_helper import get_url_domain, get_cur_domain
from utils.public_fun import send_http_request, get_timestr
from utils.utils_except import BusinessException

logger = logging.getLogger(__name__)


def get_weixin_define(wxdefine_code, appid=None):
    # 返回weixin_school对象
    if not wxdefine_code and not appid:
        return None
    weixindefine = WeixinDefine.objects.filter(del_flag=FLAG_NO)
    if wxdefine_code:
        weixindefine = weixindefine.filter(code=wxdefine_code)

    if appid:
        weixindefine = weixindefine.filter(app_id=appid)

    weixindefine = weixindefine.first()

    # 检查必配字段
    if not weixindefine or not weixindefine.app_id or not weixindefine.app_secret or weixindefine.only_request_openid is None:
        raise Exception(u'微信定义缺少必配字段。')

    return weixindefine


def get_weixin_global_access_token(weixindefine):
    if not weixindefine:
        raise BusinessException(ERR_GET_APPID)
    now_time = datetime.datetime.now()
    # 如果accesstoken过期了则重新获取
    if not weixindefine.access_token or not weixindefine.access_token_update_time or \
            get_timestr(weixindefine.access_token_update_time) <= get_timestr(now_time):
        logger.info('weixin_global_access_token need update')
        update_weixin_global_access_token(weixindefine)
        weixindefine = get_weixin_define(settings.WEIXIN_DEFINECODE_JS)
    cur_access_token = weixindefine.access_token
    return cur_access_token


def update_weixin_global_access_token(weixindefine):
    if not weixindefine:
        raise BusinessException(ERR_GET_APPID)
    global_access_token_url = 'https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid=' + weixindefine.app_id + '&secret=' + weixindefine.app_secret
    # globalaccesstokeninfo = requests.get(global_access_token_url).text
    globalaccesstokeninfo = send_http_request(url=global_access_token_url, method="GET")
    globalaccesstokeninfo = json.loads(globalaccesstokeninfo)
    now_time = datetime.datetime.now()

    if globalaccesstokeninfo.get('access_token'):
        weixindefine.access_token = globalaccesstokeninfo.get('access_token')
        weixindefine.access_token_update_time = now_time + datetime.timedelta(seconds=int(globalaccesstokeninfo.get('expires_in'))/2)
        weixindefine.save()
        # print settings.weixin_access_token_updatetime.strftime("%Y-%m-%d %H:%M:%S")
    else:
        # 获取accesstoken失败
        raise Exception(globalaccesstokeninfo)
    return globalaccesstokeninfo


def get_account_byjsopenid(openid):
    # 通过竞赛网openid获取帐户信息
    weixinaccount = WeixinAccount.objects.filter(openid=openid, del_flag=FLAG_NO).first()
    if not weixinaccount:
        return None

    account = weixinaccount.account
    return account


def get_account_byfhopenid(fhopenid):
    # 通过fhopenid获取帐户信息
    weixinaccount = WeixinAccount.objects.filter(openid_fh=fhopenid, del_flag=FLAG_NO).first()
    if not weixinaccount:
        return None

    account = weixinaccount.account
    return account


def get_rand_code():
    return uuid.uuid4().hex


def get_str_qrcode_base64(src_str):
    img = qrcode.make(src_str, border=1)
    fbuffer = cStringIO.StringIO()
    img.save(fbuffer)
    qrcode_base64 = base64.b64encode(fbuffer.getvalue())
    return qrcode_base64


# def wx_get_bind_qrcode(request, testparam1):
#     result = dict()
#
#     # 清除原来旧的记录
#     WeixinScanConfirm.objects.filter(account=request.user, busitype=WEIXIN_SCAN_TYPE_OLDUSERBIND, del_flag=FALSE_INT).update(del_flag=TRUE_INT)
#
#     # 生成新的二维码记录
#     confirm_code = get_rand_code()
#
#     weixinscanconfirm = WeixinScanConfirm()
#     weixinscanconfirm.code = confirm_code
#     weixinscanconfirm.state = ''
#     weixinscanconfirm.openid = ''
#     weixinscanconfirm.openid_fh = ''
#     weixinscanconfirm.status = WEIXIN_CONFIRM_STATUS_NONE
#     weixinscanconfirm.account = request.user
#     weixinscanconfirm.busitype = WEIXIN_SCAN_TYPE_OLDUSERBIND
#     weixinscanconfirm.save()
#     # return HttpResponseForbidden(u'<h1>Forbidden<br/> confirm_code = %s</h1>' % confirm_code)
#     # return HttpResponseRedirect('/page/olduserbind/pc?confirm_code=%s' % confirm_code)
#     cur_domain = get_cur_domain(request)
#
#     qrcode_url = 'http://%s/wx/page/scan/qrcode?confirm_code=%s&busitype=%s' % (cur_domain, confirm_code, WEIXIN_SCAN_TYPE_OLDUSERBIND)
#     logger.info(qrcode_url)
#     qrcode_img_base64 = get_str_qrcode_base64(qrcode_url)
#
#     result = {
#         "confirm_code": confirm_code,
#         "base64_image": qrcode_img_base64,
#         "base64_html": r'<img src="data:image/gif;base64,' + qrcode_img_base64 + '">',
#     }
#
#     return result


def wx_get_qrcode(request, busitype):
    result = dict()

    # 如果是老用户绑定，清除原来旧的记录
    if int(busitype) == WEIXIN_SCAN_TYPE_OLDUSERBIND:
        WeixinScanConfirm.objects.filter(account=request.user, busitype=busitype, del_flag=FALSE_INT).update(del_flag=TRUE_INT)

    # 生成新的二维码记录
    confirm_code = get_rand_code()

    # 安全起见，还是校验一下重复，也可能一辈子都走不到这个逻辑上来
    update_cnt = WeixinScanConfirm.objects.filter(code=confirm_code, del_flag=FALSE_INT).update(del_flag=TRUE_INT)
    if update_cnt:
        logger.info(u'一定要记录下这历史性的一刻！confirm_code=%s' % confirm_code)

    weixinscanconfirm = WeixinScanConfirm()
    weixinscanconfirm.code = confirm_code
    weixinscanconfirm.state = ''
    weixinscanconfirm.openid = ''
    weixinscanconfirm.openid_fh = ''
    weixinscanconfirm.status = WEIXIN_CONFIRM_STATUS_NONE
    weixinscanconfirm.account = request.user if int(busitype) == WEIXIN_SCAN_TYPE_OLDUSERBIND else None
    weixinscanconfirm.busitype = busitype
    weixinscanconfirm.save()
    # return HttpResponseForbidden(u'<h1>Forbidden<br/> confirm_code = %s</h1>' % confirm_code)
    # return HttpResponseRedirect('/page/olduserbind/pc?confirm_code=%s' % confirm_code)
    cur_domain = get_cur_domain(request)

    # qrcode_url = 'http://%s/wx/page/scan/qrcode?confirm_code=%s&busitype=%s' % (cur_domain, confirm_code, busitype)
    # 先拿竞赛网和烽火两个公众号的openid
    state_url = 'http://%s/wx/page/scan/qrcode?confirm_code=%s' % (cur_domain, confirm_code)
    param_dict = {
        "state": state_url,
    }
    param_str = urlencode(param_dict)
    qrcode_url = "http://%s/wx/authorize?%s" % (cur_domain, param_str)

    logger.info(qrcode_url)
    qrcode_img_base64 = get_str_qrcode_base64(qrcode_url)

    result = {
        "confirm_code": confirm_code,
        "base64_image": qrcode_img_base64,
        "base64_html": r'<img src="data:image/gif;base64,' + qrcode_img_base64 + '">',
    }

    return result


def wx_get_qrcode_scan_status(request, confirm_code, timeout=10):
    result = dict()
    weixinscanconfirm = WeixinScanConfirm.objects.filter(code=confirm_code, del_flag=FALSE_INT,
                                                         create_time__gte=(datetime.datetime.now()-datetime.timedelta(minutes=timeout))).first()
    if not weixinscanconfirm:
        raise BusinessException(ERR_QRCODE_TIMEOUT)

    result['status'] = weixinscanconfirm.status
    result['desc'] = weixinscanconfirm.desc

    return result


def wx_update_scan_status(request, confirm_code, confirm_status):
    result = dict()
    weixinscanconfirm = WeixinScanConfirm.objects.filter(code=confirm_code, del_flag=FALSE_INT).first()
    if not weixinscanconfirm:
        raise BusinessException(ERR_QRCODE_TIMEOUT)

    weixinscanconfirm.status = confirm_status
    weixinscanconfirm.save()

    return result


def wx_page_scan_qrcode(request, confirm_code):
    result = dict()
    weixinscanconfirm = WeixinScanConfirm.objects.filter(code=confirm_code, del_flag=FALSE_INT).first()
    if not weixinscanconfirm:
        raise BusinessException(ERR_QRCODE_TIMEOUT)

    weixinscanconfirm.status = WEIXIN_CONFIRM_STATUS_CONFING
    weixinscanconfirm.save()

    cur_domain = get_cur_domain(request)
    if weixinscanconfirm.busitype == WEIXIN_SCAN_TYPE_OLDUSERBIND:
        # 老用户绑定流程，跳转到绑定页面
        # qrcode_url = 'http://%s/wx/mobile/scan/code/olduserbind?confirm_code=%s&mobile=%s' % (cur_domain, confirm_code, weixinscanconfirm.account.mobile)
        qrcode_url = 'http://%s/weixin/wxHandle?type=%s&confirm_code=%s&mobile=%s' % (cur_domain, weixinscanconfirm.busitype, confirm_code, weixinscanconfirm.account.mobile)
        return HttpResponseRedirect(qrcode_url)
    elif weixinscanconfirm.busitype == WEIXIN_SCAN_TYPE_REG:
        # 检查微信是否已经注册过
        old_weixinaccount = WeixinAccount.objects.filter(openid=weixinscanconfirm.openid, del_flag=FALSE_INT)
        if old_weixinaccount:
            # 更新确认状态
            weixinscanconfirm.status = WEIXIN_CONFIRM_STATUS_ERROR
            weixinscanconfirm.desc = ERR_WEIXIN_IS_BIND[1]
            weixinscanconfirm.save()
            raise BusinessException(ERR_WEIXIN_IS_BIND)

        # qrcode_url = 'http://%s/wx/mobile/scan/code/reg?confirm_code=%s&mobile=%s' % (cur_domain, confirm_code, '')
        qrcode_url = 'http://%s/weixin/wxHandle?type=%s&confirm_code=%s&mobile=%s' % (cur_domain, weixinscanconfirm.busitype, confirm_code, '')
        return HttpResponseRedirect(qrcode_url)
    elif weixinscanconfirm.busitype == WEIXIN_SCAN_TYPE_LOGIN:
        # 检查微信是否已经注册过
        old_weixinaccount = WeixinAccount.objects.filter(openid=weixinscanconfirm.openid, del_flag=FALSE_INT)
        if not old_weixinaccount:
            # 更新确认状态
            weixinscanconfirm.status = WEIXIN_CONFIRM_STATUS_ERROR
            weixinscanconfirm.desc = ERR_WEIXIN_IS_NOT_BIND[1]
            weixinscanconfirm.save()
            raise BusinessException(ERR_WEIXIN_IS_NOT_BIND)

        # qrcode_url = 'http://%s/wx/mobile/scan/code/reg?confirm_code=%s&mobile=%s' % (cur_domain, confirm_code, '')
        qrcode_url = 'http://%s/weixin/wxHandle?type=%s&confirm_code=%s&mobile=%s' % (cur_domain, weixinscanconfirm.busitype, confirm_code, '')
        return HttpResponseRedirect(qrcode_url)
    else:
        raise BusinessException(ERR_WEIXIN_BUSITYPE)


def wx_page_scan_bind_sure(request, confirm_code):
    result = dict()
    weixinscanconfirm = WeixinScanConfirm.objects.filter(code=confirm_code, del_flag=FALSE_INT, busitype=WEIXIN_SCAN_TYPE_OLDUSERBIND).first()
    if not weixinscanconfirm:
        raise BusinessException(ERR_QRCODE_TIMEOUT)

    # 检查用户是否已经绑定微信，绑定规则如下
    # 如果已经绑定自己，则提示已经注册
    # 如果绑定其它微信（非本次扫码的微信），则绑定后，将微信更新为新的微信
    # 如果未绑定的其它微信，但是扫码微信绑定了其它帐户，则将微信绑定到当前帐户，原帐户取消微信绑定。
    cur_user_weixinaccount = WeixinAccount.objects.filter(account=weixinscanconfirm.account, del_flag=FALSE_INT).first()
    old_weixinbind_weixinaccount = WeixinAccount.objects.filter(openid=weixinscanconfirm.openid, del_flag=FALSE_INT).first()
    if not cur_user_weixinaccount:
        # 检查当前微信是否绑定了别的帐户，如果绑定了，先将其它帐户进行解绑
        if old_weixinbind_weixinaccount:
            old_weixinbind_weixinaccount.del_flag = TRUE_INT
            old_weixinbind_weixinaccount.save()

        # 未绑定微信的，直接绑定用户微信
        weixinaccount = WeixinAccount()
        weixinaccount.account = weixinscanconfirm.account
        weixinaccount.openid = weixinscanconfirm.openid
        weixinaccount.openid_fh = weixinscanconfirm.openid_fh
        weixinaccount.save()

        # 更新确认状态
        weixinscanconfirm.status = WEIXIN_CONFIRM_STATUS_CONFIRM
        weixinscanconfirm.desc = ''
        weixinscanconfirm.save()

    elif cur_user_weixinaccount.openid == weixinscanconfirm.openid:
        # 已经绑定，并且绑定的微信就是当前扫码需要绑定的微信

        # 更新确认状态
        weixinscanconfirm.status = WEIXIN_CONFIRM_STATUS_ERROR
        weixinscanconfirm.desc = ERR_WEIXIN_IS_BIND[1]
        weixinscanconfirm.save()
        raise BusinessException(ERR_WEIXIN_IS_BIND)

    else:
        # 如果已经绑定微信，且绑定的微信不同，先将当前微信解绑，再将当前微信绑到当前帐户。
        if old_weixinbind_weixinaccount:
            old_weixinbind_weixinaccount.del_flag = TRUE_INT
            old_weixinbind_weixinaccount.save()

        cur_user_weixinaccount.openid = weixinscanconfirm.openid
        cur_user_weixinaccount.openid_fh = weixinscanconfirm.openid_fh
        cur_user_weixinaccount.save()

        # 更新确认状态
        weixinscanconfirm.status = WEIXIN_CONFIRM_STATUS_CONFIRM
        weixinscanconfirm.desc = ''
        weixinscanconfirm.save()

    cur_domain = get_cur_domain(request)
    # mobile_sure_url = 'http://%s/wx/mobile/scan/sure' % cur_domain
    mobile_sure_url = 'http://%s/weixin/wxResult?isSuccess=true&type=%s' % (cur_domain, weixinscanconfirm.busitype)
    return HttpResponseRedirect(mobile_sure_url)

    # if weixinscanconfirm.busitype == WEIXIN_SCAN_TYPE_OLDUSERBIND:
    #     # 老用户绑定流程，跳转到绑定页面
    #     state = 'http://%s/wx/mobile/scan/sure' % cur_domain
    #
    #     param_dict = {
    #         "state": state,
    #         "confirm_code": confirm_code,
    #     }
    #     param_str = urllib.urlencode(param_dict)
    #     get_weixincode_url = 'http://%s/wx/authorize?%s' % (cur_domain, param_str)
    #
    #     return HttpResponseRedirect(get_weixincode_url)
    # return result


def wx_page_scan_reg_sure(request, confirm_code):
    # 用户扫码注册
    # 检查确认码是否注册生成的
    weixinscanconfirm = WeixinScanConfirm.objects.filter(code=confirm_code, del_flag=FALSE_INT, busitype=WEIXIN_SCAN_TYPE_REG).first()
    if not weixinscanconfirm:
        raise BusinessException(ERR_QRCODE_TIMEOUT)

    # 检查微信是否已经注册过
    old_weixinaccount = WeixinAccount.objects.filter(openid=weixinscanconfirm.openid, del_flag=FALSE_INT)
    if old_weixinaccount:
        # 更新确认状态
        weixinscanconfirm.status = WEIXIN_CONFIRM_STATUS_ERROR
        weixinscanconfirm.desc = ERR_WEIXIN_IS_BIND[1]
        weixinscanconfirm.save()
        raise BusinessException(ERR_WEIXIN_IS_BIND)

    # 手机直接跳转成功页面
    cur_domain = get_cur_domain(request)
    # mobile_sure_url = 'http://%s/wx/mobile/scan/sure' % cur_domain
    mobile_sure_url = 'http://%s/weixin/wxResult?isSuccess=true&type=%s' % (cur_domain, weixinscanconfirm.busitype)
    return HttpResponseRedirect(mobile_sure_url)


def wx_page_scan_login_sure(request, confirm_code):
    # 检查确认码是否登陆生成的
    weixinscanconfirm = WeixinScanConfirm.objects.filter(code=confirm_code, del_flag=FALSE_INT, busitype=WEIXIN_SCAN_TYPE_LOGIN).first()
    if not weixinscanconfirm:
        raise BusinessException(ERR_QRCODE_TIMEOUT)

    # 更新确认状态
    weixinscanconfirm.status = WEIXIN_CONFIRM_STATUS_CONFIRM
    weixinscanconfirm.desc = ''
    weixinscanconfirm.save()

    # 手机直接跳转成功页面
    cur_domain = get_cur_domain(request)
    # mobile_sure_url = 'http://%s/wx/mobile/scan/sure' % cur_domain
    mobile_sure_url = 'http://%s/weixin/wxResult?isSuccess=true&type=%s' % (cur_domain, weixinscanconfirm.busitype)
    return HttpResponseRedirect(mobile_sure_url)


def wx_page_scan_sure(request, confirm_code):
    weixinscanconfirm = WeixinScanConfirm.objects.filter(code=confirm_code, del_flag=FALSE_INT).first()
    if not weixinscanconfirm:
        raise BusinessException(ERR_QRCODE_TIMEOUT)

    if weixinscanconfirm.busitype == WEIXIN_SCAN_TYPE_OLDUSERBIND:
        return wx_page_scan_bind_sure(request, confirm_code)
    elif weixinscanconfirm.busitype == WEIXIN_SCAN_TYPE_REG:
        return wx_page_scan_reg_sure(request, confirm_code)
    elif weixinscanconfirm.busitype == WEIXIN_SCAN_TYPE_LOGIN:
        return wx_page_scan_login_sure(request, confirm_code)
    else:
        raise BusinessException(ERR_WEIXIN_BUSITYPE)
