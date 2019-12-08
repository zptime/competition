# -*- coding=utf-8 -*-
from django.db import models

from applications.activity.models import Ranks
from utils.utils_db import AdvancedModel
from ..team.models import Team, TeamExpert
from ..work.models import Work


class Score(AdvancedModel):
    work = models.ForeignKey(Work, verbose_name=u'作品', on_delete=models.PROTECT)
    team_expert = models.ForeignKey(TeamExpert, verbose_name=u'分组专家', on_delete=models.PROTECT)
    score = models.IntegerField(default=-1, blank=True, null=True, verbose_name=u'分数')
    # level = models.CharField(default="", max_length=30, verbose_name=u'等级')
    rank = models.ForeignKey(Ranks, blank=True, null=True, verbose_name=u'作品等级', default=None, on_delete=models.PROTECT)
    status = models.IntegerField(default=0, choices=((1, u"已提交"), (0, u"未提交")), verbose_name=u'评审状态')
    comments = models.CharField(default="", max_length=256, verbose_name=u'评语')

    class Meta:
        db_table = "score"
        verbose_name_plural = u"分数"
        verbose_name = u"分数"

    def __unicode__(self):
        return str(self.id)


class FinalScore(AdvancedModel):
    work = models.ForeignKey(Work, verbose_name=u'作品', on_delete=models.PROTECT)
    team_expert = models.ForeignKey(TeamExpert, blank=True, null=True, verbose_name=u'分组专家', on_delete=models.PROTECT)
    score = models.IntegerField(default=-1, blank=True, null=True, verbose_name=u'分数')
    # level = models.CharField(default="", max_length=30, verbose_name=u'等级')
    rank = models.ForeignKey(Ranks, blank=True, null=True, verbose_name=u'作品等级', default=None, on_delete=models.PROTECT)
    status = models.IntegerField(default=0, choices=((1, u"已提交"), (0, u"未提交")), verbose_name=u'评审状态')
    comments = models.CharField(default="", max_length=256, verbose_name=u'评语')

    class Meta:
        db_table = "final_score"
        verbose_name_plural = u"最终分数"
        verbose_name = u"最终分数"

    def __unicode__(self):
        return unicode(self.id)
