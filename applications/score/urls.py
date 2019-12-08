# -*- coding=utf-8 -*-

from django.conf.urls import url

from applications.score.views import *


urlpatterns = [
    url(r"^api/edit/score/?$", api_edit_score),
    url(r"^api/detail/score/?$", api_detail_score),
    url(r"^api/submit/score/?$", api_submit_score),
]
