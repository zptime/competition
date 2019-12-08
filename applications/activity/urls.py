#!/usr/bin python
# coding=utf-8

from django.conf.urls import url
from views import *

urlpatterns = [
    url("^api/list/activity/create/area/?$", api_list_activity_create_area),  # 获取可创建活动的区域列表
    url("^api/list/activity/category/?$", api_list_activity_category),  # 赛事中心活动列表
    url("^api/list/activity/?$", api_list_activity),  # 系统全部赛事活动（开放展示）

    url("^api/add/template/?$", api_add_template),  # 创建模板（新创建和从已有活动创建）
    url("^api/list/template/?$", api_list_template),  # 模板列表
    url("^api/delete/template/?$", api_delete_template),  # 删除模板
    url("^api/add/activity/?$", api_add_activity),  # 利用模板增加一个新活动
    url("^api/edit/activity/?$", api_edit_activity),  # 修改模板 / 修改活动 / 切换活动阶段
    url("^api/detail/activity/?$", api_detail_activity),  # 活动基本信息详情
    url("^api/delete/activity/?$", api_delete_activity),  # 删除活动

    url("^api/edit/rank/?$", api_edit_ranks),  # 编辑奖项
    url("^api/detail/rank/?$", api_detail_ranks),  # 奖项列表

    url("^api/edit/rule/?$", api_edit_rule),  # 编辑评审规则 获取评审规则详情
    url("^api/detail/rule/?$", api_detail_rule),  # 获取评审规则详情

    # url("^api/edit/work_attr/schema/?$", api_edit_work_attr_schema),  # 更新作品信息属性定义  暂时不用
    url("^api/edit/work_attr/schema/bulk/?$", api_edit_work_attr_schema_bulk),  # 批量更新作品信息属性定义
    url("^api/detail/work_attr/?$", api_detail_work_attr),  # 查看活动的属性信息定义
    url("^api/detail/work_attr/schema/?$", api_detail_work_attr_schema),  # 查看活动的属性信息定义

    url("^api/add/activity_role/exist/?$", api_add_activity_role_exist),  # 向活动中添加用户
    url("^api/add/activity_role/registered/?$", api_add_activity_role_registered),
    url("^api/add/activity_role/new/?$", api_add_activity_role_new),
    url("^api/add/activity_role/import/?$", api_add_activity_role_import),
    url("^api/export/activity_role/?$", api_export_activity_role),
    url("^api/download/activity_role/template/?$", api_download_activity_role_template),
    url("^api/list/activity_role/?$", api_list_activity_role),  # 查询活动中的用户
    url("^api/detail/activity_role/?$", api_detail_activity_role),  # 查看活动中用户详情
    url("^api/remove/activity_role/?$", api_remove_activity_role),  # 从活动中移除若干用户
    url("^api/available/user/add/role/?$", api_available_user_add_role),  # 可添加的用户（从用户库中判断）
    url("^api/available/registered/add/role/?$", api_available_registered_add_role),  # 可添加的用户（从注册用户中判断）
    url("^api/edit/activity_role/?$", api_edit_activity_role), # 修改活动中用户的信息

    url("^api/add/activity_expert/exist/?$", api_add_activity_expert_exist),  # 向活动中添加专家
    url("^api/add/activity_expert/new/?$", api_add_activity_expert_new),  # 向活动中新建并添加专家
    url("^api/add/activity_expert/import/?$", api_import_activity_expert),  # 导入专家
    url("^api/list/activity_expert/?$", api_list_activity_expert),  # 列出活动的评审者信息
    url("^api/delete/activity_expert/?$", api_delete_activity_expert),  # 从活动中移除若干专家
    url("^api/available/add/activity_expert/?$", api_available_add_activity_expert),

    url("^api/export/activity_expert/?$", api_export_activity_expert),  # 导出专家
    url("^api/download/activity_expert/template/?$", api_download_expert_template),  # 下载专家模板

    url(r'^api/import/winner/?$', api_import_winner),
    url(r'^api/list/winner/?$', api_list_winner),

    url(r'^api/tag/alias/?$', api_tag_alias),

    # url(r'^api/signup/?$', api_signup), # 用户自行报名参加
]