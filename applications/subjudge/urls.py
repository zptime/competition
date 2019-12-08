# coding=utf-8

from django.conf.urls import url
from applications.subjudge.views import *


urlpatterns = [
    url(r"^api/subjudge/control/?$", api_control_subjudge),  # 启动或者停止子级评审
    url(r"^api/subjudge/decide/?$", api_decide_subjudge),
    url(r"^api/subjudge/detail/?$", api_detail_subjudge),

    url(r"^api/subjudge/expert/add/?$", api_add_expert),
    url(r"^api/subjudge/expert/new/?$", api_new_expert),
    url(r"^api/subjudge/expert/remove/?$", api_remove_expert),
    url(r"^api/subjudge/expert/list/?$", api_list_expert),
    url(r"^api/subjudge/expert/available/add/?$", api_available_add_expert),
    url(r"^api/subjudge/expert/export/?$", api_export_expert),
    url(r"^api/subjudge/expert/import/?$", api_import_expert),

    url(r"^api/subjudge/team/list/?$", api_list_team),
    url(r"^api/subjudge/team/list/judger/?$", api_list_team_judger),
    url(r"^api/subjudge/team/export/?$", api_export_team),
    url(r"^api/subjudge/team/detail/?$", api_detail_team),
    url(r"^api/subjudge/team/edit/?$", api_edit_team),
    url(r"^api/subjudge/team/delete/?$", api_delete_team),

    url(r"^api/subjudge/team_work/add/?$", api_add_team_work),
    url(r"^api/subjudge/team_work/remove/?$", api_remove_team_work),
    url(r"^api/subjudge/team_work/list/?$", api_subjudge_work_in_team),
    url(r"^api/subjudge/team_work/available/add/?$", api_subjudge_work_availale_add_team),

    url(r"^api/subjudge/work/for/expert/?$", api_subjudge_list_work_for_expert),
    url(r"^api/subjudge/work/for/leader/?$", api_subjudge_list_work_for_leader),
    url(r"^api/subjudge/work/export/for/expert/?$", api_subjudge_export_work_for_expert),
    url(r"^api/subjudge/work/export/for/leader/?$", api_subjudge_export_work_for_leader),

    url(r"^api/subjudge/team_expert/update/?$", api_update_team_expert),
    url(r"^api/subjudge/team_expert/area/?$", api_area_stats_team_expert),
    url(r"^api/subjudge/team_expert/available/add/?$", api_available_add_team_expert),

    url(r"^api/subjudge/score/edit/?$", api_edit_score),
    url(r"^api/subjudge/score/detail/?$", api_detail_score),
    url(r"^api/subjudge/score/submit/?$", api_submit_score),

]