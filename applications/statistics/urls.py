# -*- coding=utf-8 -*-

from django.conf.urls import url

from applications.statistics.views import *


urlpatterns = [
    url(r"^api/list/total_statistics$", api_list_total_statistics),
    url(r"^api/list/country_statistics$", api_list_country_statistics),
    url(r"^api/list/level_statistics$", api_list_level_statistics),
]
