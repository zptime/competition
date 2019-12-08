#!/usr/bin/python
# -*- coding=utf-8 -*-

from django.contrib import admin
from models import *


class AccountAppAdmin(admin.ModelAdmin):
    list_display = ['id', 'username', 'name']
    # list_filter = ['id', 'username', 'name']
    search_fields = ['username', 'name']
    exclude = ('encoded_pwd', 'last_login', 'image')
    actions = ['qry_password']

    def save_model(self, request, obj, form, change):
        if 'pbkdf2_sha256' not in obj.password:
            obj.encoded_pwd = xor_crypt_string(data=obj.password, encode=True)
            obj.set_password(obj.password)
        obj.num = obj.username
        obj.save()

    def qry_password(self, request, queryset):
        if queryset.count() < 1:
            self.message_user(request, u'请选择一条或多条记录查询密码')

        result = ''
        for eachrow in queryset:
            result = result + u'%s:%s\n\n' % (eachrow.username, xor_crypt_string(data=eachrow.encoded_pwd, decode=True))

        self.message_user(request, result)
    qry_password.short_description = u'查询用户密码'

admin.site.register(Account, AccountAppAdmin)


class AreaAppAdmin(admin.ModelAdmin):
    list_display = ["id", "area_code", "area_level", "area_name", 'parent_id', 'del_flag']
    list_filter = ['id', 'area_code', 'del_flag']
admin.site.register(Area, AreaAppAdmin)


class UserAppAdmin(admin.ModelAdmin):
    list_display = ['id', 'account_id', 'area_id', 'name', 'sex', 'del_flag']
    list_filter = ['id', 'del_flag', 'name']

admin.site.register(User, UserAppAdmin)
