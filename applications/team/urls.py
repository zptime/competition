# -*- coding=utf-8 -*-

from django.conf.urls import url

from applications.team.views import *


urlpatterns = [
    url(r"^api/list/team/super/?$", api_list_team_by_super),
    url(r"^api/export/team/super/?$", api_export_team_by_super),
    url(r"^api/list/team/judger/?$", api_list_team_by_judger),

    url(r"^api/edit/team/?$", api_edit_team),
    url(r"^api/delete/team/?$", api_delete_team),
    url(r"^api/detail/team/?$", api_detail_team),

    url(r"^api/add/team_work/?$", api_add_team_work),
    url(r"^api/remove/team_work/?$", api_remove_team_work),

    url(r"^api/available/add/expert/in/team/?$", api_available_add_expert_in_team),
    url(r"^api/list/expert/area/in/team/?$", api_list_expert_area_in_team),
    url(r"^api/update/expert/in/team/?$", api_update_expert_in_team),

]
