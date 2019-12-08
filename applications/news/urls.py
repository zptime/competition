# -*- coding=utf-8 -*-

from django.conf.urls import url
from applications.news.views import *

urlpatterns = [

    url(r"^api/list/news$", api_list_news),
    url(r"^api/add/news$", api_add_news),
    url(r"^api/detail/news$", api_detail_news),
    url(r"^api/update/news$", api_update_news),
    url(r"^api/operate/news$", api_operate_news),

    url(r"^api/list/newstype$", api_list_newstype),
    url(r"^api/add/newstype$", api_add_newstype),
    url(r"^api/update/newstype$", api_update_newstype),
    url(r"^api/delete/newstype$", api_delete_newstype),

    url(r"^api/list/focusnews$", api_list_focusnews),  # 焦点新闻，即首页新闻轮播图

]
