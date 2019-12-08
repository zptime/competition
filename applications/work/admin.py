# -*- coding=utf-8 -*-
from django.contrib import admin
from models import *


class WorkAppAdmin(admin.ModelAdmin):
    list_display = ['activity',  'no', 'name', 'sub_activity', 'phase', 'project', 'del_flag']
    list_filter = ['name', 'del_flag']

admin.site.register(Work, WorkAppAdmin)


class WorkFileObjAppAdmin(admin.ModelAdmin):
    list_display = ['work',  'src_file', 'des_file', 'img_file', 'del_flag']
    list_filter = ['work', 'del_flag']

admin.site.register(WorkFileObj, WorkFileObjAppAdmin)


class WorkAttrStringAppAdmin(admin.ModelAdmin):
    list_display = ['work',  'attr', 'value', 'del_flag']
    list_filter = ['work', 'del_flag']

admin.site.register(WorkAttrString, WorkAttrStringAppAdmin)