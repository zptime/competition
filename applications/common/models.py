# -*- coding=utf-8 -*-

import json
import types

from django.db import models

from applications.activity.models import Activity
from applications.subjudge.models import SubJudge
from applications.user.models import Account
from utils.const_def import *
from utils.utils_db import AdvancedManager, AdvancedModel

TASK_STATUS_WAIT = -1  # 未开始
TASK_STATUS_SUCC = 1  # 已完成
TASK_STATUS_FAIL = 2  # 已失败
TASK_STATUS_DOING = 0  # 进行中

TASK_EXPORT_WORK_BY_CREATOR = 'export_work_by_creator'   # 活动创建者导出所有作品


class TaskTrace(AdvancedModel):
    account = models.ForeignKey(Account, on_delete=models.PROTECT, verbose_name=u"相关用户")
    activity = models.ForeignKey(Activity, on_delete=models.PROTECT, verbose_name=u"活动")
    subjudge = models.ForeignKey(SubJudge, blank=True, null=True, on_delete=models.PROTECT, verbose_name=u"子级评审")
    name = models.CharField(u'任务名称', max_length=50)
    body = models.TextField(u'任务参数', default='')
    status = models.IntegerField(u"任务状态", default=TASK_STATUS_WAIT,
                        choices=((TASK_STATUS_WAIT, u"未开始"), (TASK_STATUS_DOING, u"进行中")
                                 ,(TASK_STATUS_SUCC, u"已完成"), (TASK_STATUS_FAIL, u"已失败")))
    progress = models.CharField(u'任务进度', default='0', max_length=10)
    result = models.CharField(u'任务结果', blank=True, null=True, max_length=300)
    output = models.TextField(u'任务产出', blank=True, null=True)

    class Meta:
        db_table = "task"
        verbose_name_plural = u"任务追踪"
        verbose_name = u"任务追踪"

    def __unicode__(self):
        return u"任务追踪(%s)" % self.id
