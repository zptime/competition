#!/usr/bin python
# coding=utf-8

from models import Expert
from django.contrib import admin


class ExpertAppAdmin(admin.ModelAdmin):
    list_display = ['id', "account_id", "area_id", "del_flag"]
    list_filter = ['id', 'del_flag', 'account_id']
admin.site.register(Expert, ExpertAppAdmin)
