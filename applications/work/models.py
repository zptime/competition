# -*- coding=utf-8 -*-
import logging
from django.db import models
from applications.activity.models import Activity, Ranks, Role
from applications.upload_resumable.models import FileObj
from utils.const_def import *
from utils.utils_db import AdvancedModel
from ..user.models import Account, Area, User
from ..team.models import Team, TeamExpert

logger = logging.getLogger(__name__)


class Work(AdvancedModel):
    activity = models.ForeignKey(Activity, verbose_name=u'活动', on_delete=models.PROTECT)
    no = models.CharField(default="", max_length=30, verbose_name=u'编号')
    name = models.CharField(default="", max_length=256, verbose_name=u'名称')
    sub_activity = models.CharField(default="", blank=True, max_length=30, verbose_name=u'子活动')
    phase = models.CharField(default="", blank=True, max_length=30, verbose_name=u'学段')
    project = models.CharField(default="", blank=True, max_length=30, verbose_name=u'项目')
    subject = models.CharField(default="", blank=True,  max_length=30, verbose_name=u'学科')
    introduction = models.CharField(default="", blank=True,  max_length=512, verbose_name=u'作品简介')  # 文档转码时从登记表中读取
    status = models.IntegerField(default=WORK_STATUS_NOT_UPLOAD[0], blank=True, verbose_name=u'状态')

    # approval_status = models.CharField(default="", max_length=256, verbose_name=u'审批状态')
    # is_publish = models.IntegerField(default=0, choices=((1, u"是"), (0, u"否")), verbose_name=u'是否发布')
    pv = models.IntegerField(default=0, blank=True, verbose_name=u'浏览次数')
    like = models.IntegerField(default=0, blank=True, verbose_name=u'点赞次数')
    vote = models.IntegerField(default=0, blank=True, verbose_name=u'投票次数')
    team = models.ForeignKey(Team, null=True, blank=True, verbose_name=u'分组', on_delete=models.PROTECT)
    ranks = models.ForeignKey(Ranks, null=True, blank=True, verbose_name=u'评级', on_delete=models.PROTECT)
    final_score = models.IntegerField(default=0, null=True, blank=True, verbose_name=u'分数')
    authors = models.CharField(default="", blank=True, max_length=256, verbose_name=u'作者')  # 上传/修改作品时更新该字段
    author_school = models.CharField(default="", blank=True, max_length=256, verbose_name=u'作者学校')  # 上传/修改作品时更新该字段
    uploader = models.ForeignKey(User, verbose_name=u'上传者', on_delete=models.PROTECT)   # 上传作品时更新该字段
    # city = models.CharField(default="", blank=True, max_length=30, verbose_name=u'市州')  # 上传作品时更新该字段
    # country = models.CharField(default="", blank=True, max_length=30, verbose_name=u'区县')  # 上传作品时更新该字段
    # institution = models.CharField(default="", blank=True, max_length=30, verbose_name=u'机构')  # 上传作品时更新该字段
    area = models.ForeignKey(Area, default=PROVINCE_AREA_ID, verbose_name=u'地区名称', on_delete=models.PROTECT)
    rar_file = models.ForeignKey(FileObj, null=True, blank=True, verbose_name=u'文件对象', related_name="rar_file_relation", on_delete=models.PROTECT)
    task_status = models.IntegerField(default=0, choices=TASK_STATUS_CHOICE, verbose_name=u'任务状态')
    task_time = models.DateTimeField(null=True, blank=True, verbose_name=u'任务开始处理时间')
    task_output = models.CharField(default="", blank=True,  max_length=256, verbose_name=u'任务处理输出')

    # 预览相关 由后台任务填写这组字段
    preview_status = models.IntegerField(default=0, choices=WORK_PREVIEW_STATUS_CHOICE, verbose_name=u'预览状态')
    img_file = models.ForeignKey(FileObj, null=True, blank=True, verbose_name=u'预览图片', related_name="img_file_relation", on_delete=models.PROTECT)

    commit_time = models.DateTimeField(u'提交时间', null=True, blank=True)
    is_public = models.IntegerField(default=0, choices=((1, u"是"), (0, u"否")), verbose_name=u'是否发布')

    class Meta:
        db_table = "work"
        verbose_name_plural = u"作品"
        verbose_name = u"作品"

    def __unicode__(self):
        return self.name


class WorkFlow(AdvancedModel):
    work = models.ForeignKey(Work, verbose_name=u'作品', on_delete=models.PROTECT)
    pre_flow = models.ForeignKey('self', verbose_name=u'上一个流程', blank=True, null=True, related_name="pre", on_delete=models.PROTECT)
    trigger = models.ForeignKey(Role, verbose_name=u'事件触发者', on_delete=models.PROTECT)
    trigger_fullname = models.CharField(u'姓名', max_length=20, blank=True, null=True)
    event = models.CharField(u'事件', max_length=20, blank=True, null=True)
    area = models.ForeignKey(Area, verbose_name=u'当前所在区域', on_delete=models.PROTECT)
    area_name = models.CharField(u'地区名称', max_length=40, blank=True, null=True)
    work_status = models.IntegerField(default=0, blank=True, null=True, verbose_name=u'状态')

    def handler(self):
        result = list()
        users = User.objects.filter(del_flag=FALSE_INT, area=self.area)
        for u in users:
            if Role.objects.filter(user=u, activity=self.work.activity).exists():
                result.append(u)
        logger.info('work(%s,%s) can handled by %s' % (self.work.id, self.work.name, ','.join([each.account.name for each in result])))
        return result

    class Meta:
        db_table = "work_flow"
        verbose_name_plural = u"作品周转"
        verbose_name = u"作品周转"

    def __unicode__(self):
        return self.id


class WorkFileObj(AdvancedModel):
    work = models.ForeignKey(Work, verbose_name=u'作品', on_delete=models.PROTECT)
    src_file = models.ForeignKey(FileObj, verbose_name=u'原始文件', related_name="src_file", on_delete=models.PROTECT)
    des_file = models.ForeignKey(FileObj,  null=True, blank=True, verbose_name=u'转换后文件', related_name="des_file", on_delete=models.PROTECT)
    img_file = models.ForeignKey(FileObj, null=True, blank=True,  verbose_name=u'转换后文件', related_name="img_file", on_delete=models.PROTECT)
    task_status = models.IntegerField(default=0, choices=TASK_STATUS_CHOICE, verbose_name=u'任务状态')
    task_time = models.DateTimeField(null=True, blank=True, verbose_name=u'任务开始处理时间')
    task_output = models.CharField(default="", blank=True,  max_length=512, verbose_name=u'任务处理输出')
    permission = models.IntegerField(default=FILE_PERMISSION_ALL[0], choices=FILE_PERMISSION_CHOICE, verbose_name=u'文件预览权限')

    class Meta:
        db_table = "work_file_obj"
        verbose_name_plural = u"作品文件"
        verbose_name = u"作品文件"

    def __unicode__(self):
        return self.id


class WorkAttr(AdvancedModel):
    activity = models.ForeignKey(Activity, verbose_name=u'活动', on_delete=models.PROTECT)
    category = models.IntegerField(u'类别', choices=((1, u"作品其它信息"), (2, u"作者信息"), (3, u"指导教师")))
    # group_sn 用于表示作者和指导老师的第一或第二属性
    group_sn = models.IntegerField(u"组号", default=1)
    sn = models.IntegerField(u'组别内序号', default=1)

    name = models.CharField(u'名称', default="", max_length=50)
    type = models.IntegerField(u'输入类型', default=1, choices=((1, u"输入框"), (2, u"序列")))
    values = models.CharField(u'备选值', default="", blank=True, max_length=254)
    mandatory = models.IntegerField(u'是否必填', default=0, choices=((1, u"是"), (0, u"否")))

    class Meta:
        db_table = "work_attr"
        verbose_name_plural = u"作品属性"
        verbose_name = u"作品属性"

    def __unicode__(self):
        return self.name


class WorkAttrString(AdvancedModel):
    work = models.ForeignKey(Work, verbose_name=u'作品', on_delete=models.PROTECT)
    attr = models.ForeignKey(WorkAttr, verbose_name=u'属性', on_delete=models.PROTECT)
    value = models.CharField(default="", max_length=512, verbose_name=u'值')

    class Meta:
        db_table = "work_attr_string"
        verbose_name_plural = u"作品属性值"
        verbose_name = u"作品属性值"

    def __unicode__(self):
        return self.id


class WorkVote(AdvancedModel):
    work = models.ForeignKey(Work, verbose_name=u'作品', on_delete=models.PROTECT)
    account = models.ForeignKey(Account, related_name="star_account", on_delete=models.PROTECT, verbose_name=u"相关用户")
    num = models.IntegerField(u'票数', default=1)  # 预留，当前只支持每人投一票
    desc = models.CharField(default="", max_length=512, verbose_name=u'描述')

    class Meta:
        db_table = "work_vote"
        verbose_name_plural = u"作品投票"
        verbose_name = u"作品投票"

    def __unicode__(self):
        return self.id
