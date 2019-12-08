#!/usr/bin python
# coding=utf-8

from django.conf.urls import url

from views import *

urlpatterns = [
    url("^api/list/expert_user", api_list_expert_user),
    url("^api/add/expert_user", api_add_expert_user),
    url("^api/mod/expert_user", api_mod_expert_user),
    url("^api/delete/expert_user", api_delete_expert_user),
    url("^api/detail/expert", api_detail_expert),

]