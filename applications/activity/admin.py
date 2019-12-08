#!/usr/bin python
# coding=utf-8

from models import *
from django.contrib import admin


class ActivityAppAdmin(admin.ModelAdmin):
    list_display = ["id", "user_id", 'name', "stage", 'template_flag', 'del_flag']
    list_filter = ['id', 'stage', 'name', 'del_flag']
admin.site.register(Activity, ActivityAppAdmin)


# class SubActivityAttrAppAdmin(admin.ModelAdmin):
#     list_display = ['id', 'activity_id', 'sub_ac_name', 'del_flag']
#     list_filter = ["id", "activity_id", 'del_flag']
# admin.site.register(SubActivityAttr, SubActivityAttrAppAdmin)


class RoleAppAdmin(admin.ModelAdmin):
    list_display = ['id', "activity_id", "user_id", "del_flag"]
    list_filter = ['id', 'del_flag']
admin.site.register(Role, RoleAppAdmin)


class ExpertActivityAppAdmin(admin.ModelAdmin):
    list_display = ["id", 'activity_id', 'expert_id', 'del_flag']
    list_filter = ['id', 'del_flag']
admin.site.register(ExpertActivity, ExpertActivityAppAdmin)
