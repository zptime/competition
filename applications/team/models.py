# -*- coding=utf-8 -*-
from django.db import models

from applications.activity.models import Activity
from applications.expert.models import Expert
from utils.utils_db import AdvancedModel
from ..user.models import Account


class Team(AdvancedModel):
    activity = models.ForeignKey(Activity, verbose_name=u'活动', on_delete=models.PROTECT)
    name = models.CharField(default="", blank=True, max_length=30, verbose_name=u'名称')
    work_count = models.IntegerField(default=0, verbose_name=u'作品数量')

    class Meta:
        db_table = "team"
        verbose_name_plural = u"分组"
        verbose_name = u"分组"

    def __unicode__(self):
        return self.name


class TeamExpert(AdvancedModel):
    team = models.ForeignKey(Team, verbose_name=u'分组', on_delete=models.PROTECT)
    expert = models.ForeignKey(Expert, verbose_name=u'专家', on_delete=models.PROTECT)
    sn = models.IntegerField(verbose_name=u'序号')
    is_leader = models.IntegerField(default=0, choices=((1, u"是"), (0, u"否")), verbose_name=u'是否组长')

    class Meta:
        db_table = "team_expert"
        verbose_name_plural = u"分组专家"
        verbose_name = u"分组专家"

    def __unicode__(self):
        return unicode(self.id)


# class TeamWork(models.Model):
#     team = models.ForeignKey(Team, verbose_name=u'分组')
#     work = models.ForeignKey(Work, verbose_name=u"作品")
#
#     create_time = models.DateTimeField(auto_now_add=True, verbose_name=u'创建时间')
#     update_time = models.DateTimeField(auto_now=True, verbose_name=u'修改时间')
#     del_flag = models.IntegerField(default=0, choices=((1, u"是"), (0, u"否")), verbose_name=u'是否删除')
#
#     class Meta:
#         db_table = "team_work"
#         verbose_name_plural = u"分组作品"
#         verbose_name = u"分组作品"
#
#     def __unicode__(self):
#         return self.id
