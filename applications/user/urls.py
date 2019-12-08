# -*- coding=utf-8 -*-

from django.conf.urls import url

from views import *

urlpatterns = [
    # url(r'^api/common/upload/image', api_upload_image),  # 图片上传
    url("^api/login", api_login),
    url("^api/logout", api_logout),
    url("^api/detail/account", api_detail_account),
    url("^api/list/user", api_list_user),
    url("^api/check/username", api_check_username),
    url("^api/add/user", api_add_user),
    url("^api/mod/user", api_mod_user),
    url("^api/reset/others_password", api_reset_others_password),
    url("^api/reset/own_password", api_reset_own_password),
    url("^api/reset/forget_password", api_reset_forget_password),  # 新增
    url("^api/delete/user", api_delete_user),
    url("^api/list/sub_area", api_list_sub_area),
    url("^api/config/user", api_config_user),
    url("^api/add/account$", api_add_account),
    # url("^api/get/current_user$", api_get_current_user),  # V3版本废弃本接口
    url("^api/get/activity_user$", api_get_activity_user),  # 已修改
    # url("^api/get/area_onhome", api_get_area_onhome),  # 不用改, 此接口废弃
    url("^api/get/area_byid", api_get_area_byid),

    # url(r"^api/import/user$", api_import_user),
    # url(r"^api/import/activity_user$", api_import_activity_user),
    # url(r"^api/export/user$", api_export_user),
    # url(r"^api/export/expert$", api_export_expert),
    # url(r"^api/export/activity_user$", api_export_activity_user),
    # url(r"^api/export/activity_expert$", api_export_activity_expert),
    # url(r"^api/download/user_template$", api_download_user_template),
    # url(r"^api/download/activity_user_template$", api_download_activity_user_template),

    # 用户创建活动权限
    url(r"^api/list/account$", api_list_account),
    url(r"^api/list/account_right$", api_list_account_right),
    url(r"^api/add/account_right$", api_add_account_right),
    url(r"^api/del/account_right$", api_del_account_right),

    # 用户自己相关
    url("^api/account/reg$", api_account_reg),
    url("^api/account/dataconfirm$", api_account_dataconfirm),
    url("^api/mod/account$", api_mod_account),
    url("^api/send/smsverifycode$", api_send_smsverifycode),
    url("^api/check/smsverifycode$", api_check_smsverifycode),

    url("^api/list/region$", api_list_region),
    url("^api/update/region_fullname$", api_update_region_fullname),
    url("^api/update/area_fullname$", api_update_area_fullname),
    url("^api/qry/institution_reg$", api_qry_institution_reg),  # 学校机构注册用户查询

    url("^api/qry/area/dropdowndetail$", api_qry_area_dropdowndetail),  # 查询地区下拉框详情
]
