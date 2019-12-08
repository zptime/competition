#!/usr/bin/env python
# coding=utf-8
import json
import types

from django.db import models

from competition_v3.settings.base import DEFAULT_WORK_FILE_SIZE_MAX
from utils.const_def import *
from utils.utils_db import AdvancedManager, AdvancedModel
from ..user.models import Account, User
from ..expert.models import Expert
from ..upload_resumable.models import FileObj


class Activity(AdvancedModel):
    user = models.ForeignKey(User, blank=True, null=True, related_name='activity_account', on_delete=models.PROTECT, verbose_name=u"创办者")
    name = models.CharField(default="", blank=True, null=True, max_length=100, verbose_name=u'活动名称')

    upload_time = models.DateTimeField(blank=True, null=True, verbose_name=u'上传时间')
    group_time = models.DateTimeField(blank=True, null=True, verbose_name=u'分组时间')
    review_time = models.DateTimeField(blank=True, null=True, verbose_name=u'评审时间')
    public_time = models.DateTimeField(blank=True, null=True, verbose_name=u'公示时间')
    archive_time = models.DateTimeField(blank=True, null=True, verbose_name=u"归档时间")

    stage = models.IntegerField(u'活动阶段', default=ACTIVITY_STAGE_EDIT, choices=
            ((ACTIVITY_STAGE_EDIT, u"创建"), (ACTIVITY_STAGE_UPLOAD, u"上传"), (ACTIVITY_STAGE_GROUP, u"分组"),
            (ACTIVITY_STAGE_REVIEW, u"评审"), (ACTIVITY_STAGE_PUBLIC, u"公示"), (ACTIVITY_STAGE_ARCHIVE, u"归档")))

    banner = models.ForeignKey(FileObj, related_name='r_banners', null=True, blank=True, verbose_name=u'banner图片', on_delete=models.PROTECT)
    organizers = models.CharField(default="", max_length=256, verbose_name=u'主办方')
    participator = models.CharField(default="", max_length=256, verbose_name=u'参赛对象')
    introduction = models.TextField(default="", blank=True, verbose_name=u'活动介绍')
    attachment = models.ForeignKey(FileObj, related_name='r_attachments', blank=True, null=True, verbose_name=u'附件', on_delete=models.PROTECT)

    copyright = models.TextField(u'版权声明', blank=True, null=True)
    is_top = models.IntegerField(u"置顶", default=0, choices=((1, u"是"), (0, u"否")))
    is_minor = models.IntegerField(u"首页不显示", default=0, choices=((1, u"是"), (0, u"否")))
    genre = models.IntegerField(u"活动类型", default=ACTIVITY_GENRE_1,
                        choices=((ACTIVITY_GENRE_1, u"全流程活动"), (ACTIVITY_GENRE_2, u"仅展示型活动")))

    author_count = models.IntegerField(default=3, verbose_name=u'作者数量')
    tutor_count = models.IntegerField(default=3, verbose_name=u'指导教师数量')

    # 级联信息提取
    sub_ac_flag = models.IntegerField(default=0, choices=((0, u"否"), (1, u"是")), verbose_name=u"是否有子活动标志")
    base_info_value = models.CharField(default="", max_length=2048, verbose_name=u"基本信息(学段-项目)")

    template_flag = models.IntegerField(u"是否是模板", default=0, choices=((0, u"否"), (1, u"是")))
    template_based = models.IntegerField(u"基于的模板ID", null=True, blank=True)

    browse_count = models.BigIntegerField(u"浏览次数", default=0)
    work_count = models.PositiveIntegerField(u"作品个数", default=0)

    open_time = models.DateTimeField(blank=True, null=True, verbose_name=u'活动发布时间')

    @staticmethod
    def _get_upload_size_limit(sub_obj, phase, project):
        ph_list = sub_obj['period_list']
        for each_ph in ph_list:
            if each_ph['period'] == phase:
                prj_list = each_ph['item_list']
                for each_prj in prj_list:
                    if isinstance(each_prj, types.DictType):
                        if each_prj['name'] == project:
                            return each_prj['size']
                    else:
                        return str(DEFAULT_WORK_FILE_SIZE_MAX)
        return ''

    def get_upload_size_limit(self, sub_activity, phase, project):
        base_info = json.loads(self.base_info_value)
        if sub_activity:
            for each_sub in base_info:
                if each_sub['ac_type'] == sub_activity:
                    return self._get_upload_size_limit(each_sub, phase, project)
            return ''
        else:
            acti = base_info[0]
            return self._get_upload_size_limit(acti, phase, project)

    class Meta:
        db_table = "activity"
        verbose_name_plural = u"活动"
        verbose_name = u"活动"

    def __unicode__(self):
        return self.name


class Rule(AdvancedModel):
    activity = models.ForeignKey(Activity, on_delete=models.PROTECT, verbose_name=u"活动")
    code = models.IntegerField(u"规则编号", default=REVIEW_RULE_1,
                        choices=((REVIEW_RULE_1, u"组长制"), (REVIEW_RULE_2, u"平均分制")))
    content = models.TextField(u'规则内容(json)')

    def parse_rule(self):
        from applications.score.rule import JudgeRule
        return JudgeRule.get_rule(self.id, activity_id=self.activity.id, code=self.code, content=self.content)

    class Meta:
        db_table = "rule"
        verbose_name_plural = u"评审规则"
        verbose_name = u"评审规则"

    def __unicode__(self):
        return u"评审规则(%s)" % self.code


class Ranks(AdvancedModel):
    activity = models.ForeignKey(Activity, related_name='ranks_activity', on_delete=models.PROTECT, verbose_name=u"活动")
    sn = models.IntegerField(u"等级序号", default=1)
    name = models.CharField(u"等级名称", default='', blank=True, max_length=16)
    all_allowed = models.IntegerField(u"评审可用", default=1, choices=((0, u"是"), (1, u"否")))
    # shown_onpage = models.IntegerField(default=0, choices=((0, u"是"), (1, u"否")), verbose_name=u"是否显示在首页")  # 废弃

    class Meta:
        db_table = "ranks"
        verbose_name = u"等级"
        verbose_name_plural = u"等级"

    def __unicode__(self):
        return str(self.id)


class Role(AdvancedModel):
    activity = models.ForeignKey(Activity, related_name='role_activity', on_delete=models.PROTECT, verbose_name=u"活动")
    user = models.ForeignKey(User, related_name='role_user', on_delete=models.PROTECT, verbose_name=u"参赛用户")
    parent_role = models.ForeignKey('self', blank=True, null=True, on_delete=models.PROTECT, verbose_name=u"上级组织者")
    max_work = models.SmallIntegerField(u"最大允许上报作品数", blank=True, null=True)
    approve_work = models.SmallIntegerField(u"当前已提交或审核的作品数", default=0)

    class Meta:
        db_table = 'role'
        verbose_name = u"活动参与者"
        verbose_name_plural = u"活动参与者"

    def __unicode__(self):
        return str(self.id)


class ExpertActivity(AdvancedModel):
    activity = models.ForeignKey(Activity, on_delete=models.PROTECT, verbose_name=u"活动")
    expert = models.ForeignKey(Expert, on_delete=models.PROTECT, verbose_name=u"专家")

    class Meta:
        db_table = 'expert_activity'
        verbose_name = u"活动专家"
        verbose_name_plural = u"活动专家"

    def __unicode__(self):
        return str(self.id)


class Alias(AdvancedModel):
    # 该表仅可从后台修改
    activity = models.ForeignKey(Activity, on_delete=models.PROTECT, verbose_name=u"活动")
    attr = models.CharField(u"字段", max_length=80)
    alias = models.CharField(u"别名", null=True, blank=True, max_length=80)

    class Meta:
        db_table = 'alias'
        verbose_name = u"别名"
        verbose_name_plural = u"别名"

    def __unicode__(self):
        return str(self.id)


class Winner(AdvancedModel):
    activity = models.ForeignKey(Activity, on_delete=models.PROTECT, verbose_name=u"活动")
    uuid = models.CharField(u"唯一标识", max_length=80, default="")
    sn = models.IntegerField(u"序号", default=1)
    attr = models.TextField(default="", blank=True, verbose_name=u'获奖者信息详情')

    class Meta:
        db_table = 'winner'
        verbose_name = u"获奖名单"
        verbose_name_plural = u"获奖名单"

    def __unicode__(self):
        return str(self.id)
