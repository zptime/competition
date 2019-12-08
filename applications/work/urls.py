# -*- coding=utf-8 -*-

from django.conf.urls import url

from applications.work.agents import api_public_work, api_list_publicwork
from applications.work.views import *


urlpatterns = [
    url(r'^api/create/work/?$', api_create_work),
    url(r'^api/submit/work/?$', api_submit_work),
    url(r'^api/update/work/?$', api_update_work),

    url(r'^api/list/work/super/?$', api_list_work_super),
    url(r'^api/export/work/super/?$', api_export_work_super),
    url(r'^api/export/work/super/all/?$', api_export_work_super_all),
    url(r'^api/export/work/super/download/?$', api_export_work_super_download),
    url(r'^api/list/work/manager/?$', api_list_work_manager),
    url(r'^api/export/work/manager/?$', api_export_work_manager),
    url(r'^api/list/work/upload/?$', api_list_work_upload),
    url(r'^api/export/work/upload/?$', api_export_work_upload),
    url(r'^api/list/work/expert/?$', api_list_work_expert),
    url(r'^api/export/work/expert/?$', api_export_work_expert),
    url(r'^api/list/work/leader/?$', api_list_work_leader),
    url(r'^api/export/work/leader/?$', api_export_work_leader),
    url(r'^api/list/work/team/?$', api_list_work_in_team),
    url(r'^api/list/available/add/work/team/?$', api_list_work_avalable_add_team),

    url(r'^api/delete/work/?$', api_delete_work),
    url(r'^api/detail/work/?$', api_detail_work),
    url(r'^api/download/work_template/?$', api_download_work_template),
    url(r'^api/import/work/?$', api_import_work),
    url(r'^api/approve/work/?$', api_approve_work),
    url(r'^api/reject/work/?$', api_reject_work),
    url(r'^api/rank/work/?$', api_rank_work),  # 给作品评奖，仅活动创建者可用
    url(r'^api/star/work/?$', api_star_work),  # 点赞
    url(r'^api/vote/work/?$', api_vote_work),  # 投票
    url(r'^api/download/work/?$', api_download_work),
    url(r'^api/match/work/?$', api_match_work),  # 匹配作品和文件（批量）

    url(r'^api/list/no_file_work/?$', api_list_no_file_work),
    url(r'^api/get/outsimipic/?$', api_get_outsimipic),

    url(r'^api/public/work/?$', api_public_work),
    url(r'^api/list/public_work/?$', api_list_publicwork),

    url(r'^api/workflow/?$', api_workflow),  # 仅供调试
    url(r'^api/approve/count/?$', api_approve_count),  # 仅供调试
]
