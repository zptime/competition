# -*- coding=utf-8 -*-

from django.conf import settings
from django.db import models


class OperateLog(models.Model):
    account_id = models.IntegerField(u'用户账号', blank=True, null=True)
    user_type = models.PositiveSmallIntegerField(u'用户类型', blank=True, null=True,
                choices=((0, u'未设置'), (1, u'学生'), (2, u'教师'), (4, u'家长')))
    user_school_id = models.PositiveSmallIntegerField(u'用户学校', blank=True, null=True)
    request = models.TextField(u'请求内容', blank=True, null=True)
    head = models.TextField(u'请求头', blank=True, null=True)
    method = models.CharField(u'请求方法', default='', max_length=5, blank=True, null=True)
    url = models.TextField(u'URL', default='')
    response = models.TextField(u'响应内容', blank=True, null=True)
    c = models.IntegerField(u'业务返回码', default=0, blank=True, null=True)
    m = models.TextField(u'业务返回信息', blank=True, null=True)
    status_code = models.CharField(u'响应码', max_length=10, blank=True, null=True)
    ua = models.TextField(u'UA', blank=True, null=True)
    version = models.CharField(u'终端版本号', max_length=50, blank=True, null=True)
    ip = models.CharField(u'ip地址', max_length=30, blank=True, null=True)
    request_time = models.DateTimeField(u'请求时间', blank=True, null=True)
    response_time = models.DateTimeField(u'响应时间', blank=True, null=True)
    duration = models.IntegerField(u'操作时长（毫秒）', default=0, blank=True, null=True)
    create_time = models.DateTimeField(u'日志创建时间', auto_now_add=True)

    class Meta:
        db_table = settings.LOG_CENTER.get('table', 'common_oper_log')
        verbose_name_plural = u'请求日志表'
        verbose_name = u'请求日志表'
        ordering = ['-create_time']

    def __unicode__(self):
        return 'Log(url: %s)' % self.url

