# -*- coding=utf-8 -*-

from django.conf.urls import url

from views import *

urlpatterns = [
    # url(r'^api/common/upload/image', api_upload_image),  # 图片上传
    # 下面两个接口比较危险，用于测试使用，否则有安全问题。上线时请关闭
    url(r'^update/access_token$', update_weixin_global_access_token),  # 微信强制刷新全局access_token
    url(r'^get/access_token$', get_weixin_global_access_token),  # 微信获取全局access_token

    # 获取用户资料，判断用户绑等信息，不直接由前台调用，由后台控制页面跳转流程。
    url(r'^MP_verify_jIjfmE2UW1zSOJPc.txt$', wx_get_verifyfile),  # 微信烽火公众号域名验证
    url(r'^MP_verify_ySQKawRcgCbi0lzA.txt$', wx_get_jswverifyfile),  # 微信竞赛网公众号域名验证
    url(r'^wx/authorize$', wx_get_code),  # 获取用户资料前，先获取code
    url(r'^wx/access_token$', wx_code_to_access_token),  # 根据code获取用户信息
    url(r'^wx/authorize_fh$', wx_get_code_fh),  # 获取烽火openid对应的code
    url(r'^wx/access_token_fh$', wx_code_to_access_token_fh),  # 根据烽火code获取用户openid
    url(r'^wx/authorize_fhlogin$', wx_get_code_fhlogin),  # 扫码获得烽火公众号openid后直接登陆系统。本步骤为先获取code
    url(r'^wx/access_token_fhlogin$', wx_code_to_access_token_fhlogin),  # 扫码获得烽火公众号openid后直接登陆系统。

    # url(r'^pc/scanlogin$', wx_pc_scanlogin),  # pc端扫码登陆
    url(r'^wx/page/scan/qrcode$', wx_page_scan_qrcode),  # 微信扫码后处理逻辑，用于更新状态，跳转到相应业务页面
    # url(r'^wx/page/scan/bind/sure$', wx_page_scan_bind_sure),  # 微信扫码后点击了确认
    url(r'^wx/page/scan/sure$', wx_page_scan_sure),  # 微信扫码后点击了确认

    url(r'^api/wx/get/qrcode/scan/status$', wx_get_qrcode_scan_status),  # 前端轮询二维码扫码状态
    url(r'^api/wx/update/scan/status$', wx_update_scan_status),  # 更新用户扫码状态
    url(r'^api/wx/get/qrcode$', wx_get_qrcode),  # 获取老用户绑定微信二维码

]
