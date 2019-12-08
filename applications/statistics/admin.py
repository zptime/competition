#!/usr/bin/python
# -*- coding=utf-8 -*-

from django.contrib import admin
from models import *


class AreaWorkNumberAppAdmin(admin.ModelAdmin):
    list_display = ["id", "activity", "area", "work_number", 'del_flag']
    list_filter = ['id', 'area', 'del_flag']
admin.site.register(AreaWorkNumber, AreaWorkNumberAppAdmin)


class SubjectWorkNumberAppAdmin(admin.ModelAdmin):
    list_display = ["id", "activity", "subject", "work_number", 'del_flag']
    list_filter = ['id', 'subject', 'del_flag']
admin.site.register(SubjectWorkNumber, SubjectWorkNumberAppAdmin)


class PhaseWorkNumberAppAdmin(admin.ModelAdmin):
    list_display = ["id", "activity", "phase", "work_number", 'del_flag']
    list_filter = ['id', 'phase', 'del_flag']
admin.site.register(PhaseWorkNumber, PhaseWorkNumberAppAdmin)


class ProjectWorkNumberAppAdmin(admin.ModelAdmin):
    list_display = ["id", "activity", "project", "work_number", 'del_flag']
    list_filter = ['id', 'project', 'del_flag']
admin.site.register(ProjectWorkNumber, ProjectWorkNumberAppAdmin)