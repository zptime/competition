#!/usr/bin/env python
# coding=utf-8

from django.contrib import admin
from models import *


class NewsAppAdmin(admin.ModelAdmin):
    list_display = ["id", "title", "news_type_id", "publisher_id", "is_top", "status", 'del_flag']
    list_filter = ["id", "news_type_id", "is_top", "status", "del_flag"]

admin.site.register(News, NewsAppAdmin)
