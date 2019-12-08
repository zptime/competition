# coding=utf-8
from django.db import models
from utils.const_def import *
from utils.utils_db import AdvancedModel
from applications.activity.models import Activity
from applications.expert.models import Expert
from applications.user.models import User, Area
from applications.work.models import Work


class SubJudge(AdvancedModel):
    activity = models.ForeignKey(Activity, verbose_name=u'活动', on_delete=models.PROTECT)
    user = models.ForeignKey(User, verbose_name=u'子级管理员', on_delete=models.PROTECT)
    area = models.ForeignKey(Area, verbose_name=u"地区", on_delete=models.PROTECT)
    is_active = models.IntegerField(u"是否激活子级评审", default=0, choices=((1, u"是"), (0, u"否")))
    status = models.SmallIntegerField(u"状态", default=1, choices=((1, u"已启动"), (0, u"未启动")))

    class Meta:
        db_table = "subjudge"
        verbose_name_plural = u"子级评审"
        verbose_name = u"子级评审"

    def __unicode__(self):
        return str(self.id)


class SubJudgeRank(AdvancedModel):
    subjudge = models.ForeignKey(SubJudge, on_delete=models.PROTECT, verbose_name=u"子级评审")
    sn = models.IntegerField(u"奖项序号", default=1)
    name = models.CharField(u"奖项名称", default='', max_length=16)
    all_allowed = models.IntegerField(u"评审可用", default=1, choices=((1, u"是"), (0, u"否")))

    class Meta:
        db_table = "subjudge_rank"
        verbose_name = u"子级评审奖项"
        verbose_name_plural = u"子级评审奖项"

    def __unicode__(self):
        return str(self.id)


class SubJudgeRule(AdvancedModel):
    subjudge = models.ForeignKey(SubJudge, on_delete=models.PROTECT, verbose_name=u"子级评审")
    code = models.IntegerField(u"规则编号", default=REVIEW_RULE_1,
                        choices=((REVIEW_RULE_1, u"组长制"), (REVIEW_RULE_2, u"平均分制")))
    content = models.TextField(u'规则内容(json)')

    def parse_rule(self):
        from applications.subjudge.subjg_rule import SubJudgeRuleDef
        return SubJudgeRuleDef.get_rule(self.id, self.subjudge, self.code, self.content)

    class Meta:
        db_table = "subjudge_rule"
        verbose_name_plural = u"子级评审规则"
        verbose_name = u"子级评审规则"

    def __unicode__(self):
        return u"评审规则(%s)" % self.code


class SubJudgeTeam(AdvancedModel):
    subjudge = models.ForeignKey(SubJudge, on_delete=models.PROTECT, verbose_name=u"子级评审")
    name = models.CharField(u'名称', default='', max_length=30)
    work_count = models.IntegerField(default=0, verbose_name=u'作品数量')

    class Meta:
        db_table = "subjudge_team"
        verbose_name_plural = u"子级评审分组"
        verbose_name = u"子级评审分组"

    def __unicode__(self):
        return str(self.id)


class SubJudgeTeamWork(AdvancedModel):
    subjudge = models.ForeignKey(SubJudge, on_delete=models.PROTECT, verbose_name=u"子级评审")
    subjudge_team = models.ForeignKey(SubJudgeTeam, on_delete=models.PROTECT, verbose_name=u"子级评审分组")
    work = models.ForeignKey(Work, verbose_name=u'作品', on_delete=models.PROTECT)
    subjudge_status = models.PositiveSmallIntegerField(default=0, choices=((1, u"是"), (0, u"否")), verbose_name=u'子级评审状态')
    final_score = models.SmallIntegerField(u'分数', blank=True, null=True)
    final_rank = models.ForeignKey(SubJudgeRank, verbose_name=u'作品等级', null=True, blank=True, on_delete=models.PROTECT)
    final_comment = models.TextField(u'批注', null=True, blank=True)

    class Meta:
        db_table = "subjudge_team_work"
        verbose_name_plural = u"子级评审作品进组"
        verbose_name = u"子级评审作品进组"

    def __unicode__(self):
        return str(self.id)


class SubJudgeExpert(AdvancedModel):
    subjudge = models.ForeignKey(SubJudge, on_delete=models.PROTECT, verbose_name=u"子级评审")
    expert = models.ForeignKey(Expert, on_delete=models.PROTECT, verbose_name=u"专家")

    class Meta:
        db_table = 'subjudge_expert'
        verbose_name = u"子级评审专家"
        verbose_name_plural = u"子级评审专家"

    def __unicode__(self):
        return str(self.id)


class SubJudgeTeamExpert(AdvancedModel):
    subjudge = models.ForeignKey(SubJudge, on_delete=models.PROTECT, verbose_name=u"子级评审")
    subjudge_team = models.ForeignKey(SubJudgeTeam, verbose_name=u'子级评审分组', on_delete=models.PROTECT)
    expert = models.ForeignKey(Expert, verbose_name=u'专家', on_delete=models.PROTECT)
    sn = models.IntegerField(u'序号', default=1)
    is_leader = models.IntegerField(default=0, choices=((1, u"是"), (0, u"否")), verbose_name=u'是否是组长')

    class Meta:
        db_table = "subjudge_team_expert"
        verbose_name_plural = u"子级评审专家进组"
        verbose_name = u"子级评审专家进组"

    def __unicode__(self):
        return str(self.id)


class SubJudgeScore(AdvancedModel):
    subjudge_team_work = models.ForeignKey(SubJudgeTeamWork, verbose_name=u'作品', on_delete=models.PROTECT)
    subjudge_team_expert = models.ForeignKey(SubJudgeTeamExpert, verbose_name=u'专家', on_delete=models.PROTECT)
    subjudge_team = models.ForeignKey(SubJudgeTeam, verbose_name=u'子级评审分组', on_delete=models.PROTECT)
    score = models.SmallIntegerField(default=-1, blank=True, null=True, verbose_name=u'分数')
    rank = models.ForeignKey(SubJudgeRank, verbose_name=u'作品等级', blank=True, null=True, default=None, on_delete=models.PROTECT)
    comment = models.TextField(u'批注', null=True, blank=True)
    status = models.IntegerField(default=0, choices=((1, u"已提交"), (0, u"未提交")), verbose_name=u'提交状态')
    is_leader = models.IntegerField(default=0, choices=((1, u"是"), (0, u"否")), verbose_name=u'是否是组长打分')

    class Meta:
        db_table = "subjudge_score"
        verbose_name_plural = u"子级评审打分"
        verbose_name = u"子级评审打分"

    def __unicode__(self):
        return str(self.id)





