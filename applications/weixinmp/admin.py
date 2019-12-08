#!/usr/bin/python
# -*- coding=utf-8 -*-

from django.contrib import admin
from models import *


class WeixinAccountAppAdmin(admin.ModelAdmin):
    list_display = ['id', 'account', 'openid', 'openid_fh', 'name', 'image_url', 'province', 'city', 'country', 'sex', 'unionid', 'del_flag']
    list_filter = ['account', 'name', 'account__mobile', 'del_flag']
    search_fields = ["name", "account__username"]

admin.site.register(WeixinAccount, WeixinAccountAppAdmin)
